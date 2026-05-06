"""Main simulation engine."""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.config import SimulationConfig
from src.agents import Firm, Worker, SkillLevel, WorkerStatus, AIAgentPool
from src.market import JobMarket, phillips_curve_wage_adjustment, compute_reservation_wage
from src.analytics import MetricsCollector, PeriodMetrics

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Main simulation engine - orchestrates all agents and market dynamics."""
    
    def __init__(self, config: SimulationConfig):
        """Initialize simulation engine.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        np.random.seed(config.random_seed)
        
        self.period = 0
        self.firms: Dict[int, Firm] = {}
        self.workers: Dict[int, Worker] = {}
        self.ai_pool = AIAgentPool()
        self.job_market = JobMarket(config)
        self.metrics = MetricsCollector(config)
        
        # Market-level state tracking
        self.market_wage_human = 1.0
        self.market_ai_cost = config.ai_wage_ratio
        self.total_output = 0.0
        self.unemployment_rate = 0.0
        
        # Demand growth tracking (grows endogenously with economy)
        self._base_market_capacity = config.output_market_capacity
        if self._base_market_capacity <= 0:
            self._base_market_capacity = 4.0 * config.initial_human_workers
        self._current_market_capacity = self._base_market_capacity
        
        # New task creation tracking (Acemoglu-Restrepo mechanism)
        self._current_human_task_floor = config.human_task_floor
        
        # Business formation tracking
        self.next_firm_id = config.num_firms  # ID counter for new firms
        self.firms_entered_this_period = 0
        self.firms_exited_this_period = 0
        self._avg_firm_profit = 0.0  # Opportunity signal for entrepreneurship
        
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Initialize firms and workers."""
        # Create firms
        for i in range(self.config.num_firms):
            self.firms[i] = Firm(i, self.config, entry_period=0)
            logger.debug(f"Created firm {i}")
        
        # Create workers - distribute between employed and unemployed
        num_employed = int(self.config.initial_human_workers * 0.95)
        num_unemployed = self.config.initial_human_workers - num_employed
        
        # Create unemployed workers
        for i in range(num_unemployed):
            skill = SkillLevel.HIGH if np.random.random() < 0.3 else SkillLevel.LOW
            self.workers[i] = Worker(i, self.config, skill_level=skill)
            self.workers[i].state.status = WorkerStatus.UNEMPLOYED
        
        # Create employed workers - distribute across firms
        for i in range(num_unemployed, num_employed + num_unemployed):
            skill = SkillLevel.HIGH if np.random.random() < 0.3 else SkillLevel.LOW
            worker = Worker(i, self.config, skill_level=skill)
            worker.state.status = WorkerStatus.EMPLOYED
            
            # Randomly assign to firms — wage set from firm's MPL
            firm_id = i % self.config.num_firms
            firm = self.firms[firm_id]
            worker.state.current_wage = firm.compute_mpl_human() * self.config.labor_share_of_mpl
            worker.state.current_firm = firm_id
            
            self.workers[i] = worker
            firm.state.human_workers_employed += 1
        
        # Set initial market wage as average of firm posted wages
        if self.firms:
            self.market_wage_human = np.mean([
                f.compute_mpl_human() * self.config.labor_share_of_mpl
                for f in self.firms.values()
            ])
        
        logger.info(f"Initialized {len(self.firms)} firms and {len(self.workers)} workers")
        logger.info(f"Initial employment: {num_employed} employed, {num_unemployed} unemployed")
    
    def _compute_market_statistics(self) -> tuple:
        """Compute unemployment and other market statistics.
        
        Returns:
            (unemployment_count, unemployment_rate, total_employment, job_vacancy_count)
        """
        unemployed = sum(
            1 for w in self.workers.values()
            if w.state.status == WorkerStatus.UNEMPLOYED
        )
        
        employed = sum(
            1 for w in self.workers.values()
            if w.state.status == WorkerStatus.EMPLOYED
        )
        
        unemployment_rate = unemployed / max(1, len(self.workers))
        
        job_vacancies = sum(
            f.state.job_openings_human for f in self.firms.values()
        )
        
        return unemployed, unemployment_rate, employed, job_vacancies
    
    def _update_aggregate_wage(self, unemployment_rate: float) -> None:
        """Update market wage as employment-weighted average of firm posted wages.
        
        With MPL-based wage posting, the market wage is now a *computed statistic*
        (the average of what firms actually post) rather than a Phillips curve output.
        This lets wages emerge from firm-level productivity and competition.
        
        Args:
            unemployment_rate: Current unemployment rate
        """
        # Compute employment-weighted average of firm posted wages
        total_human_employed = sum(
            f.state.human_workers_employed for f in self.firms.values()
        )
        
        if total_human_employed > 0:
            weighted_wage = sum(
                f.state.posted_wage_human * f.state.human_workers_employed
                for f in self.firms.values()
            ) / total_human_employed
            self.market_wage_human = max(0.1, weighted_wage)
        # else: keep previous period's wage as reference
        
        # AI cost may drift down with R&D (clamped to prevent going negative)
        avg_r_and_d = sum(f.state.accumulated_r_and_d for f in self.firms.values()) / max(1, len(self.firms))
        r_and_d_discount = min(0.8, 0.01 * avg_r_and_d)  # Cap at 80% reduction
        self.market_ai_cost = self.config.ai_wage_ratio * (1 - r_and_d_discount)
    
    def _reconcile_firm_headcounts(self) -> None:
        """Reconcile firm headcount counters with actual worker states.
        
        After worker.step() processes separations, the firm's
        human_workers_employed counter may be stale. This resets
        each firm's counter to the true number of workers whose
        current_firm matches.
        """
        # Reset all firm counters
        for firm in self.firms.values():
            firm.state.human_workers_employed = 0
        
        # Count actual workers at each firm
        for worker in self.workers.values():
            if (worker.state.status == WorkerStatus.EMPLOYED
                    and worker.state.current_firm is not None
                    and worker.state.current_firm in self.firms):
                self.firms[worker.state.current_firm].state.human_workers_employed += 1
    
    def _grow_population(self) -> None:
        """Add new workers to the labor force based on population growth rate.
        
        Converts annual growth rate to monthly and adds new unemployed
        workers to the simulation each period.
        """
        annual_rate = self.config.human_population_growth_rate
        if annual_rate <= 0:
            return
        
        # Convert annual rate to monthly: (1 + r_annual)^(1/12) - 1
        monthly_rate = (1 + annual_rate) ** (1.0 / 12.0) - 1.0
        
        # Expected new workers this period
        expected_new = len(self.workers) * monthly_rate
        
        # Stochastic rounding: floor + Bernoulli for fractional part
        n_new = int(expected_new)
        if np.random.random() < (expected_new - n_new):
            n_new += 1
        
        if n_new <= 0:
            return
        
        # Add new unemployed workers
        next_id = max(self.workers.keys()) + 1 if self.workers else 0
        for i in range(n_new):
            skill = SkillLevel.HIGH if np.random.random() < 0.3 else SkillLevel.LOW
            worker = Worker(next_id + i, self.config, skill_level=skill)
            worker.state.status = WorkerStatus.UNEMPLOYED
            self.workers[next_id + i] = worker
    
    def _grow_demand(self) -> None:
        """Grow output market capacity over time.
        
        Two components:
        1. Baseline growth (3% annual — new products, export markets)
        2. Endogenous response to output growth: when production rises faster
           than demand, it signals new products being created (phones, apps,
           streaming, etc.) that expand the market.
        
        This prevents the "output glut" problem where AI productivity gains
        crash prices because demand doesn't keep up.
        """
        annual_rate = self.config.demand_growth_rate
        if annual_rate <= 0:
            return
        
        monthly_rate = (1 + annual_rate) ** (1.0 / 12.0) - 1.0
        
        # Endogenous component: if output is approaching capacity,
        # demand expands faster (new products absorb production)
        utilization = self.total_output / max(1.0, self._current_market_capacity)
        if utilization > 0.5:
            # Above 50% utilization: demand grows faster to absorb output
            endogenous_boost = monthly_rate * (utilization - 0.5) * 2.0
        else:
            endogenous_boost = 0.0
        
        self._current_market_capacity *= (1.0 + monthly_rate + endogenous_boost)
    
    def _update_new_task_creation(self) -> None:
        """Update the human task floor based on economic complexity.
        
        As the economy grows and becomes more complex, new tasks emerge
        that require human input (AI oversight, creative direction,
        relationship management, ethical judgment, novel problem-solving).
        
        This implements the key Acemoglu & Restrepo (2018) insight:
        technology displaces workers from OLD tasks but creates NEW tasks
        where humans have comparative advantage.
        
        The rate of new task creation accelerates with AI adoption (more AI
        = more need for human oversight and new human-AI interface roles).
        """
        base_rate = self.config.new_task_creation_rate
        max_floor = self.config.human_task_floor_max
        
        if base_rate <= 0 or self._current_human_task_floor >= max_floor:
            return
        
        # New task creation rate scales with AI share of employment
        total_ai = sum(f.state.ai_workers_employed for f in self.firms.values())
        total_human = sum(f.state.human_workers_employed for f in self.firms.values())
        total_emp = total_ai + total_human
        ai_share = total_ai / max(1, total_emp)
        
        # Higher AI adoption → faster new task creation (need more oversight, etc.)
        effective_rate = base_rate * (1.0 + ai_share)
        
        self._current_human_task_floor = min(
            max_floor,
            self._current_human_task_floor + effective_rate
        )
        
        # Update config so firms see the new floor
        self.config.human_task_floor = self._current_human_task_floor
    
    def _update_human_productivity(self) -> None:
        """Update human productivity across all firms.
        
        Two components:
        1. Baseline growth (education, general tech progress): ~1.5% annual
        2. AI augmentation: humans working alongside AI become more productive.
           Higher AI share → larger productivity boost.
           This is the key mechanism through which AI RAISES wages.
        
        Example: A financial analyst with AI tools can process 3× more data,
        a developer with Copilot writes code 2× faster, etc.
        """
        base_annual = self.config.human_productivity_growth_rate
        augmentation = self.config.ai_augmentation_factor
        
        # Convert to monthly
        base_monthly = (1 + base_annual) ** (1.0 / 12.0) - 1.0
        
        for firm in self.firms.values():
            # AI augmentation: more AI coworkers → humans more productive
            total_emp = firm.state.human_workers_employed + firm.state.ai_workers_employed
            ai_share = firm.state.ai_workers_employed / max(1, total_emp)
            
            # Augmentation effect (diminishing returns via sqrt)
            ai_boost_monthly = augmentation * (ai_share ** 0.5) / 12.0
            
            # Total monthly growth
            growth = 1.0 + base_monthly + ai_boost_monthly
            firm.state.human_productivity *= growth
    
    def _update_worker_reservations(self) -> None:
        """Update worker reservation wages based on unemployment spell."""
        for worker in self.workers.values():
            if worker.state.status == WorkerStatus.UNEMPLOYED:
                ui_benefits = self.market_wage_human * self.config.ui_replacement_rate
                worker.state.reservation_wage = compute_reservation_wage(
                    ui_benefits,
                    worker.state.unemployment_duration,
                    self.config
                )
    
    def _process_poaching(self) -> int:
        """Process on-the-job search: employed workers may receive outside offers.
        
        Each employed worker has a probability (on_the_job_search_rate) of
        sampling one random firm's posted wage. If the outside wage exceeds
        their current wage by poaching_wage_threshold, they switch.
        
        This creates competitive pressure: high-productivity firms poach from
        low-productivity firms, forcing all firms to raise wages as productivity grows.
        
        Returns:
            Number of workers who switched firms
        """
        search_rate = getattr(self.config, 'on_the_job_search_rate', 0.05)
        if search_rate <= 0 or not self.firms:
            return 0
        
        switches = 0
        firm_list = list(self.firms.values())
        
        for worker in self.workers.values():
            if worker.state.status != WorkerStatus.EMPLOYED:
                continue
            
            # Stochastic: does this worker look around this period?
            if np.random.random() >= search_rate:
                continue
            
            # Sample one random firm (could be their own — in which case no switch)
            outside_firm = firm_list[np.random.randint(len(firm_list))]
            if outside_firm.agent_id == worker.state.current_firm:
                continue
            
            old_firm_id = worker.state.current_firm
            if worker.evaluate_poaching_offer(outside_firm.agent_id, outside_firm.state.posted_wage_human):
                # Update firm headcounts
                if old_firm_id in self.firms:
                    self.firms[old_firm_id].state.human_workers_employed = max(
                        0, self.firms[old_firm_id].state.human_workers_employed - 1
                    )
                outside_firm.state.human_workers_employed += 1
                switches += 1
        
        if switches > 0:
            logger.debug(f"Poaching: {switches} workers switched firms")
        
        return switches
    
    def _process_entrepreneurship_and_entry(self) -> int:
        """Process entrepreneurship decisions and create new firms.
        
        Workers who decided to become entrepreneurs in worker.step()
        create firms here. No artificial caps or saturation gates —
        entry is naturally limited by the savings threshold and
        stochastic entrepreneurship rate.
        
        Firm quality depends on founder type:
        - Opportunity founders (were employed): stronger firms
          (85-115% of incumbent median productivity)
        - Necessity founders (were unemployed): weaker firms
          (60-90% of incumbent median productivity)
        
        Returns:
            Number of new firms entered
        """
        new_firms_count = 0
        entrepreneurs = [
            (wid, w) for wid, w in self.workers.items()
            if w.state.status == WorkerStatus.ENTREPRENEUR
        ]
        
        # Median incumbent productivity as reference
        median_incumbent_prod = float(np.median([
            f.productivity_draw for f in self.firms.values()
        ])) if self.firms else 1.0
        
        for worker_id, worker in entrepreneurs:
            new_firm_id = self.next_firm_id
            self.next_firm_id += 1
            
            new_firm = Firm(new_firm_id, self.config, entry_period=self.period)
            
            # Firm quality depends on how the entrepreneur entered
            # Use current_wage as a proxy: workers who had a wage were employed
            was_employed = worker.state.current_wage > 0
            
            if was_employed:
                # Opportunity entrepreneur: draw centered at incumbent median
                new_firm.productivity_draw = max(
                    0.3,
                    median_incumbent_prod * np.random.normal(1.0, 0.15)
                )
            else:
                # Necessity entrepreneur: weaker firm
                new_firm.productivity_draw = max(
                    0.2,
                    median_incumbent_prod * np.random.normal(0.75, 0.15)
                )
            
            # High-skill founders get a small productivity bonus
            if worker.state.skill_level == SkillLevel.HIGH:
                new_firm.productivity_draw *= 1.1
            
            # Employ entrepreneur with new firm
            worker.state.status = WorkerStatus.EMPLOYED
            worker.state.current_firm = new_firm_id
            worker.state.current_wage = new_firm.compute_mpl_human() * self.config.labor_share_of_mpl
            new_firm.state.human_workers_employed = 1
            
            self.firms[new_firm_id] = new_firm
            new_firms_count += 1
            
            logger.debug(
                f"New firm {new_firm_id} entered by {'opportunity' if was_employed else 'necessity'} "
                f"entrepreneur {worker_id} (productivity: {new_firm.productivity_draw:.3f})"
            )
        
        return new_firms_count
    
    def step(self) -> None:
        """Execute one complete period of simulation.
        
        Sequence:
        1. Worker separations and state updates
        2. Clear market
        3. Update market wage
        4. Firms post jobs
        5. Workers apply
        6. Job matching
        7. Production and profits
        8. R&D decisions
        9. Business formation/exit
        10. Collect metrics
        
        Args:
            env: Simulation environment (contains market info)
        """
        # 1. Update market statistics
        unemployed_count, self.unemployment_rate, employed_count, vacancy_count = (
            self._compute_market_statistics()
        )
        
        # 2. Update market wage and worker reservation wages
        self._update_aggregate_wage(self.unemployment_rate)
        self._update_worker_reservations()
        
        # 3. Worker steps (separations, unemployment transitions)
        for worker in self.workers.values():
            worker.step(env=self)
        
        # 3b. Reconcile firm headcounts with actual worker states
        self._reconcile_firm_headcounts()
        
        # 3c. Population growth (new entrants to labor force)
        self._grow_population()
        
        # 3d. Demand growth (new products, markets, export demand)
        self._grow_demand()
        
        # 3e. New task creation (Acemoglu-Restrepo mechanism)
        self._update_new_task_creation()
        
        # 3f. Human productivity growth (education + AI augmentation)
        self._update_human_productivity()
        
        # 4. Clear and setup job market
        self.job_market.clear_market()
        
        # 5. Firms post jobs
        self.job_market.firms_post_jobs(
            self.firms,
            self.market_wage_human,
            self.market_ai_cost,
            unemployment_rate=self.unemployment_rate,
            current_market_capacity=self._current_market_capacity
        )
        
        # 6. Workers apply to jobs
        self.job_market.workers_apply(self.workers, self.unemployment_rate)
        
        # 6b. Recompute unemployment and vacancy counts AFTER separations and new postings
        unemployed_count, self.unemployment_rate, employed_count, vacancy_count = (
            self._compute_market_statistics()
        )
        
        # 7. Execute matching
        matches = self.job_market.execute_matching(
            self.workers,
            unemployed_count,
            vacancy_count
        )
        
        # 8. Allocate matches to firms
        self.job_market.allocate_matches_to_firms(self.firms, matches)
        
        # 8b. On-the-job search (poaching): employed workers sample outside offers
        self._process_poaching()
        
        # 9. Firm steps: production, profits, R&D
        # First pass: all firms produce (accumulate total output for pricing)
        self.total_output = 0.0
        for firm in self.firms.values():
            firm.produce_output()
            self.total_output += firm.state.output_produced
        
        # Compute single market-clearing price based on total supply
        output_price = self._compute_output_price()
        
        # Second pass: profits and R&D at the common price
        total_profit = 0.0
        total_vacancies = 0
        
        for firm in self.firms.values():
            profit = firm.compute_profits(output_price)
            total_profit += profit
            total_vacancies += firm.state.job_openings_human
            
            # R&D decision (Phase 4: pass period for lag tracking)
            firm.make_r_and_d_decision(current_period=self.period)
            
            # Apply lagged R&D benefits (Phase 4: benefits from 2+ periods ago)
            firm.apply_lagged_r_and_d_benefits(current_period=self.period)
        
        # Update opportunity signal for next period's entrepreneurship decisions
        self._avg_firm_profit = total_profit / max(1, len(self.firms))
        
        # 10. Process firm exits (and entry handled in business formation)
        firms_to_remove = [
            fid for fid, firm in self.firms.items()
            if firm.check_exit_condition()
        ]
        self.firms_exited_this_period = len(firms_to_remove)
        
        # Separate workers at exiting firms
        if firms_to_remove:
            exiting_set = set(firms_to_remove)
            for worker in self.workers.values():
                if (worker.state.status == WorkerStatus.EMPLOYED
                        and worker.state.current_firm in exiting_set):
                    worker.state.status = WorkerStatus.UNEMPLOYED
                    worker.state.current_firm = None
                    worker.state.current_wage = 0.0
                    worker.state.unemployment_duration = 0
        
        for fid in firms_to_remove:
            logger.debug(f"Firm {fid} exiting market")
            del self.firms[fid]
        
        # 11. Process entrepreneurship and new firm entry
        self.firms_entered_this_period = self._process_entrepreneurship_and_entry()
        
        # 12. Collect metrics
        employed_human = sum(
            f.state.human_workers_employed for f in self.firms.values()
        )
        employed_ai = sum(
            f.state.ai_workers_employed for f in self.firms.values()
        )
        
        avg_wage = (
            sum(w.state.current_wage for w in self.workers.values()
                if w.state.status == WorkerStatus.EMPLOYED)
            / max(1, employed_human)
        )
        
        metrics = PeriodMetrics(
            period=self.period,
            num_firms=len(self.firms),
            num_employed_human=employed_human,
            num_employed_ai=employed_ai,
            num_unemployed=unemployed_count,
            unemployment_rate=self.unemployment_rate,
            avg_wage_human=avg_wage,
            total_output=self.total_output,
            total_profit=total_profit,
            job_vacancies=total_vacancies,
            job_matches=len(matches),
            new_firms_entered=self.firms_entered_this_period,
            firms_exited=len(firms_to_remove),
            avg_firm_size=employed_human / max(1, len(self.firms)) if self.firms else 0
        )
        
        self.metrics.record_period(metrics)
        self.period += 1
        
        if self.period % 12 == 0:  # Log every year
            logger.info(
                f"Period {self.period}: Unemployment {self.unemployment_rate:.1%}, "
                f"Wage {self.market_wage_human:.2f}, Output {self.total_output:.1f}, "
                f"Firms {len(self.firms)}"
            )
    
    def _compute_output_price(self) -> float:
        """Compute output market price (inverse demand).
        
        P = a - a * (Q / Q_max)  where a = price intercept
        
        Q_max grows over time via _grow_demand(), reflecting
        expanding markets and new product categories.
        
        Returns:
            Output price
        """
        q_max = self._current_market_capacity
        
        a = self.config.output_price_intercept
        q_supplied = self.total_output
        
        price = a * (1.0 - q_supplied / q_max)
        return max(0.1, price)
    
    def run(self) -> pd.DataFrame:
        """Run full simulation.
        
        Returns:
            DataFrame with period-level metrics
        """
        logger.info(f"Starting simulation: {self.config.simulation_periods} periods")
        logger.info(f"Configuration: {self.config.num_firms} firms, "
                   f"{len(self.workers)} workers")
        
        try:
            for period_idx in range(self.config.simulation_periods):
                self.step()
                
                if (period_idx + 1) % max(1, self.config.simulation_periods // 10) == 0:
                    logger.info(f"Completed period {period_idx + 1}/{self.config.simulation_periods}")
        
        except Exception as e:
            logger.error(f"Simulation error at period {self.period}: {e}", exc_info=True)
            raise
        
        logger.info("Simulation complete")
        return self.metrics.get_results_dataframe()
    
    def get_aggregate_statistics(self) -> Dict:
        """Get current aggregate statistics for analysis and plotting.
        
        Returns a dict with keys matching those expected by PlotGenerator
        and DashboardBuilder (e.g. avg_wage_human, ai_employment_share,
        total_r_and_d_spending, etc.).
        """
        # Employment counts
        employed_human = sum(
            f.state.human_workers_employed for f in self.firms.values()
        )
        employed_ai = sum(
            f.state.ai_workers_employed for f in self.firms.values()
        )
        total_employment = employed_human + employed_ai
        
        # Average human wage (from employed workers)
        employed_workers = [
            w for w in self.workers.values()
            if w.state.status == WorkerStatus.EMPLOYED
        ]
        avg_wage_human = (
            sum(w.state.current_wage for w in employed_workers)
            / max(1, len(employed_workers))
        )
        
        # AI metrics
        ai_employment_share = employed_ai / max(1, total_employment)
        avg_ai_cost = (
            sum(f.state.posted_cost_ai for f in self.firms.values())
            / max(1, len(self.firms))
        ) if self.firms else 0.0
        
        # R&D metrics
        total_r_and_d_spending = sum(
            f.state.r_and_d_spending for f in self.firms.values()
        )
        
        # Firm metrics
        total_revenue = sum(f.state.revenue for f in self.firms.values())
        total_profit = sum(f.state.profits for f in self.firms.values())
        avg_profit_per_firm = total_profit / max(1, len(self.firms)) if self.firms else 0
        avg_firm_size = employed_human / max(1, len(self.firms)) if self.firms else 0
        
        # Market concentration (Herfindahl index)
        firm_sizes = [f.state.human_workers_employed for f in self.firms.values()]
        if firm_sizes and employed_human > 0:
            herfindahl_index = sum((s / employed_human) ** 2 for s in firm_sizes)
        else:
            herfindahl_index = 0.0
        
        # Productivity
        output_per_worker = self.total_output / max(1, total_employment)
        
        # Unemployed count
        num_unemployed = sum(
            1 for w in self.workers.values()
            if w.state.status == WorkerStatus.UNEMPLOYED
        )
        
        return {
            "period": self.period,
            "num_firms": len(self.firms),
            "num_employed_human": employed_human,
            "num_employed_ai": employed_ai,
            "num_unemployed": num_unemployed,
            "unemployment_rate": self.unemployment_rate,
            "avg_wage_human": avg_wage_human,
            "avg_wage_ai": avg_ai_cost,
            "ai_employment_share": ai_employment_share,
            "total_output": self.total_output,
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "avg_profit_per_firm": avg_profit_per_firm,
            "total_r_and_d_spending": total_r_and_d_spending,
            "avg_firm_size": avg_firm_size,
            "herfindahl_index": herfindahl_index,
            "output_per_worker": output_per_worker,
            "ai_cost_index": self.market_ai_cost,
            "market_wage_human": self.market_wage_human,
            "new_firms_entered": self.firms_entered_this_period,
            "firms_exited": self.firms_exited_this_period,
        }

