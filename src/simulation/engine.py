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
        
        # Business formation tracking
        self.next_firm_id = config.num_firms  # ID counter for new firms
        self.firms_entered_this_period = 0
        
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
            worker.state.current_wage = self.market_wage_human
            
            # Randomly assign to firms
            firm_id = i % self.config.num_firms
            worker.state.current_firm = firm_id
            
            self.workers[i] = worker
            self.firms[firm_id].state.human_workers_employed += 1
        
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
        """Update market wage using Phillips curve.
        
        Args:
            unemployment_rate: Current unemployment rate
        """
        # AI employment share (for dampening)
        total_employment = sum(
            f.state.human_workers_employed + f.state.ai_workers_employed
            for f in self.firms.values()
        )
        ai_employment = sum(
            f.state.ai_workers_employed for f in self.firms.values()
        )
        
        ai_share = ai_employment / max(1, total_employment)
        
        # Adjust wage using Phillips curve
        self.market_wage_human = phillips_curve_wage_adjustment(
            self.market_wage_human,
            unemployment_rate,
            natural_unemployment_rate=0.045,
            wage_adjustment_speed=self.config.wage_adjustment_speed,
            ai_employment_share=ai_share
        )
        
        # AI cost may drift (simplified)
        self.market_ai_cost = self.config.ai_wage_ratio * (
            1 - 0.01 * sum(f.state.accumulated_r_and_d for f in self.firms.values()) / max(1, len(self.firms))
        )
    
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
    
    def _process_entrepreneurship_and_entry(self) -> int:
        """Process entrepreneurship decisions and create new firms.
        
        Logic:
        1. Identify entrepreneurs (workers with status == ENTREPRENEUR)
        2. For each, evaluate whether entry succeeds (stochastic)
        3. If entry succeeds:
           - Create new firm with random productivity
           - Employ entrepreneur with that firm
           - Initialize firm with small workforce
        4. Return count of successful entries
        
        Returns:
            Number of new firms entered
        """
        new_firms_count = 0
        entrepreneurs = [
            (wid, w) for wid, w in self.workers.items()
            if w.state.status == WorkerStatus.ENTREPRENEUR
        ]
        
        for worker_id, worker in entrepreneurs:
            # Entry probability: base rate × market conditions
            # Market saturation effect: fewer firms → easier entry
            market_saturation = len(self.firms) / max(5, self.config.num_firms + 10)
            saturation_factor = 1.0 - min(0.5, 0.5 * market_saturation)
            
            entry_prob = saturation_factor  # Stochastic entry (simplified)
            
            if np.random.random() < entry_prob and new_firms_count < 2:  # Cap entries to avoid cascading
                # Create new firm
                new_firm_id = self.next_firm_id
                self.next_firm_id += 1
                
                # Productivity draw for new firm: slightly lower than average incumbent
                avg_incumbent_productivity = np.mean([
                    f.state.accumulated_r_and_d for f in self.firms.values()
                ]) if self.firms else 0.0
                
                new_productivity = max(
                    0.0,
                    avg_incumbent_productivity + np.random.normal(0, 0.1 * max(0.5, avg_incumbent_productivity))
                )
                
                new_firm = Firm(new_firm_id, self.config, entry_period=self.period)
                new_firm.state.accumulated_r_and_d = new_productivity
                
                # Employ entrepreneur with new firm
                worker.state.status = WorkerStatus.EMPLOYED
                worker.state.current_firm = new_firm_id
                worker.state.current_wage = self.market_wage_human
                worker.state.accumulated_savings = 0  # Capital used
                new_firm.state.human_workers_employed = 1  # Entrepreneur counts as employee
                
                # Add to active firms
                self.firms[new_firm_id] = new_firm
                new_firms_count += 1
                
                logger.debug(
                    f"New firm {new_firm_id} entered with entrepreneur {worker_id} "
                    f"(productivity: {new_productivity:.3f})"
                )
        
        # Reset entrepreneur status for failed entrants (back to unemployed? or employed elsewhere?)
        for worker_id, worker in entrepreneurs:
            if worker.state.status == WorkerStatus.ENTREPRENEUR:
                # Entry failed - return to unemployed
                worker.state.status = WorkerStatus.UNEMPLOYED
                worker.state.unemployment_duration = 0
                logger.debug(f"Entrepreneurship attempt by {worker_id} failed, returning to unemployment")
        
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
        
        # 4. Clear and setup job market
        self.job_market.clear_market()
        
        # 5. Firms post jobs
        self.job_market.firms_post_jobs(
            self.firms,
            self.market_wage_human,
            self.market_ai_cost
        )
        
        # 6. Workers apply to jobs
        self.job_market.workers_apply(self.workers, self.unemployment_rate)
        
        # 7. Execute matching
        matches = self.job_market.execute_matching(
            self.workers,
            unemployed_count,
            vacancy_count
        )
        
        # 8. Allocate matches to firms
        self.job_market.allocate_matches_to_firms(self.firms, matches)
        
        # 9. Firm steps: production, profits, R&D
        self.total_output = 0.0
        total_profit = 0.0
        total_vacancies = 0
        
        for firm in self.firms.values():
            # Production
            firm.produce_output()
            
            # Profit calculation (use market-derived price)
            output_price = self._compute_output_price()
            profit = firm.compute_profits(output_price)
            
            self.total_output += firm.state.output_produced
            total_profit += profit
            total_vacancies += firm.state.job_openings_human
            
            # R&D decision
            firm.make_r_and_d_decision()
        
        # 10. Process firm exits (and entry handled in business formation)
        firms_to_remove = [
            fid for fid, firm in self.firms.items()
            if firm.check_exit_condition()
        ]
        
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
        """Compute output market price (simple inverse demand).
        
        P = 1 - (Q / Q_max) where Q_max is capacity
        
        Returns:
            Output price
        """
        q_max = 100.0  # Market capacity
        q_supplied = self.total_output
        
        if q_supplied > q_max:
            price = 0.1  # Price floor
        else:
            price = 1.0 - (q_supplied / q_max)
        
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
        """Get current aggregate statistics."""
        return {
            "period": self.period,
            "num_firms": len(self.firms),
            "unemployment_rate": self.unemployment_rate,
            "market_wage_human": self.market_wage_human,
            "total_output": self.total_output,
            "firms_in_market": list(self.firms.keys()),
        }

