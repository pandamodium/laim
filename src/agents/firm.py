"""Firm agent class."""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
import logging
import numpy as np

from .base import Agent
from src.config import SimulationConfig

logger = logging.getLogger(__name__)


@dataclass
class FirmState:
    """Encapsulates firm state for easier tracking."""
    human_workers_employed: int = 0
    ai_workers_employed: int = 0
    job_openings_human: int = 0
    job_openings_ai: int = 0
    posted_wage_human: float = 1.0
    posted_cost_ai: float = 0.5
    output_produced: float = 0.0
    revenue: float = 0.0
    profits: float = 0.0
    losses_consecutive: int = 0
    capital: float = 0.0
    r_and_d_spending: float = 0.0
    accumulated_r_and_d: float = 0.0
    ai_productivity: float = 1.5
    human_productivity: float = 1.0
    entry_period: int = 0  # Period when firm entered market
    r_and_d_efficiency: float = 1.0  # Firm-specific R&D efficiency (heterogeneous)
    r_and_d_pipeline: List[Dict] = field(default_factory=list)  # Lagged R&D benefits
    r_and_d_history: Dict[int, float] = field(default_factory=dict)  # Period -> spending


class Firm(Agent):
    """Oligopolistic firm agent in labor market."""
    
    def __init__(
        self,
        firm_id: int,
        config: SimulationConfig,
        initial_capital: float = 50000.0,
        entry_period: int = 0
    ):
        """Initialize firm.
        
        Args:
            firm_id: Unique firm identifier
            config: Simulation configuration
            initial_capital: Starting capital/wealth
            entry_period: Period when firm entered (for tracking cohorts)
        """
        super().__init__(agent_id=firm_id, agent_type="firm")
        self.config = config
        
        # Draw firm-specific R&D efficiency
        r_and_d_eff_std = getattr(config, 'r_and_d_efficiency_heterogeneity', 0.20)
        r_and_d_efficiency = np.random.normal(loc=1.0, scale=r_and_d_eff_std)
        r_and_d_efficiency = max(0.5, min(2.0, r_and_d_efficiency))  # Clamp to [0.5, 2.0]
        
        self.state = FirmState(
            capital=initial_capital,
            entry_period=entry_period,
            r_and_d_efficiency=r_and_d_efficiency,
            ai_productivity=config.ai_productivity_multiplier,
        )
        # Log-normal productivity: creates right-skewed distribution with superstar firms
        dispersion = getattr(config, 'firm_productivity_dispersion', 0.5)
        if dispersion > 0:
            self.productivity_draw = np.random.lognormal(mean=0.0, sigma=dispersion)
        else:
            self.productivity_draw = 1.0
        self.history: List[Dict] = []
    
    def step(self, env) -> None:
        """Execute one period of firm behavior.
        
        Sequence:
        1. Compute labor demand
        2. Post wages and vacancies
        3. (Matching happens at market level)
        4. Hire matched workers
        5. Produce output
        6. Compute output price and profits
        7. Make R&D decision
        8. Record state
        
        Args:
            env: Simulation environment (contains market info)
        """
        # 1. Compute desired labor input given market prices
        market_wage = getattr(env, 'market_wage_human', 1.0)
        market_ai_cost = getattr(env, 'market_ai_cost', 0.5)
        
        # Firms target output to maintain market share
        output_target = 10 + self.agent_id * 5  # Simple: firm 0 targets 10, firm 1 targets 15, etc.
        
        human_demand, ai_demand = self.compute_labor_demand(
            market_wage, 
            market_ai_cost,
            output_target
        )
        self.state.job_openings_human = human_demand
        self.state.job_openings_ai = ai_demand
        
        # 2. Post wages
        self.post_wages_and_vacancies(market_wage, unemployment_rate=getattr(env, 'unemployment_rate', 0.045))
        
        # 3. Hiring happens at market level (via matching function)
        # This is called via hire_workers() after matching
        
        # 4. Produce output
        self.produce_output()
        
        # 5. Compute profits (output price from simple inverse demand)
        # P = 1 - Q/Q_max, where Q is total market output
        output_price = 0.9  # Simple: fixed price (will improve in Phase 2)
        self.compute_profits(output_price)
        
        # 6. Make R&D decision
        self.make_r_and_d_decision()
        
        # 7. Record state to history
        self.history.append(self.get_state())
    
    def compute_labor_demand(
        self,
        wage_human: float,
        cost_ai: float,
        output_target: float
    ) -> tuple[int, int]:
        """Compute optimal human and AI labor demand.
        
        Production function (additive):
            Y = A * (L_H + m * L_AI)
        
        where m = ai_productivity_multiplier.
        
        Cost minimization uses CES-style smooth substitution to avoid
        corner solutions (all-human or all-AI).  The ratio L_AI/L_H is
        derived from a CES first-order condition with the configured
        elasticity of substitution.
        
        A human task floor enforces that a minimum share of total labor
        must be human (representing oversight, creativity, physical tasks,
        relationship management — tasks that AI cannot automate). This
        implements the Acemoglu & Restrepo "new task creation" mechanism.
        
        Args:
            wage_human: Wage per human worker
            cost_ai: Cost per AI unit
            output_target: Desired output level
            
        Returns:
            (human_workers_demanded, ai_workers_demanded)
        """
        if output_target <= 0 or wage_human <= 0 or cost_ai <= 0:
            return 0, 0
        
        productivity_factor = self.productivity_draw * self.state.human_productivity
        ai_multiplier = self.config.ai_productivity_multiplier
        
        # Total effective labor needed: Y / A
        total_effective = output_target / max(productivity_factor, 0.01)
        
        # CES-style substitution ratio (smooth, avoids corners)
        sigma_sub = self.config.firm_substitution_elasticity  # e.g. 1.5
        alpha = 0.6  # Human labor share weight
        
        # Effective cost of one unit of AI-equivalent labor = cost_ai / m
        effective_ai_cost = cost_ai / max(ai_multiplier, 0.01)
        
        # CES FOC: L_AI/L_H = [(1-α)/α]^σ * (w_H / effective_ai_cost)^σ
        ai_human_ratio = ((1 - alpha) / alpha) ** sigma_sub * \
                         (wage_human / max(effective_ai_cost, 0.01)) ** sigma_sub
        
        # Split effective labor: L_H + m * (R * L_H) = total_effective
        # → L_H * (1 + m * R) = total_effective
        human_demand = total_effective / (1.0 + ai_multiplier * ai_human_ratio)
        ai_demand = ai_human_ratio * human_demand
        
        # Enforce human task floor: some tasks MUST be done by humans
        # (oversight, creativity, physical presence, relationship management)
        human_task_floor = getattr(self.config, 'human_task_floor', 0.20)
        total_workers = human_demand + ai_demand
        if total_workers > 0:
            human_share = human_demand / total_workers
            if human_share < human_task_floor:
                # Redistribute: humans get at least the floor share
                human_demand = total_workers * human_task_floor
                ai_demand = total_workers * (1.0 - human_task_floor)
        
        return max(0, int(np.round(human_demand))), max(0, int(np.round(ai_demand)))
    
    def compute_mpl_human(self) -> float:
        """Compute marginal product of human labor.
        
        From additive production Y = A * (L_H + multiplier * L_AI):
            MPL_H = A * human_productivity
            
        This is the value a firm gets from one additional human worker.
        
        Returns:
            Marginal product of human labor
        """
        return self.productivity_draw * self.state.human_productivity
    
    def post_wages_and_vacancies(self, market_wage_human: float, unemployment_rate: float = 0.045) -> None:
        """Post wages based on firm's marginal product of labor.
        
        Firm sets human wage as a fraction of its MPL, adjusted by
        labour market tightness (cyclical Phillips-curve-like effect).
        Higher-productivity firms naturally post higher wages.
        
        Args:
            market_wage_human: Prevailing market wage (used as reference/floor)
            unemployment_rate: Current unemployment rate (for cyclical adjustment)
        """
        mpl = self.compute_mpl_human()
        labor_share = getattr(self.config, 'labor_share_of_mpl', 0.65)
        
        # Cyclical adjustment: tight labour market → firms offer more of MPL
        # At NAIRU (4.5%), adjustment is 0. Below NAIRU → positive. Above → negative.
        nairu = 0.045
        tightness_adjustment = -0.5 * (unemployment_rate - nairu)  # ±~2.5% for 5pp gap
        tightness_adjustment = max(-0.1, min(0.1, tightness_adjustment))  # Cap at ±10%
        
        # Base posted wage = MPL × labor_share × (1 + tightness) + small noise
        noise = 1.0 + 0.02 * np.random.normal(0, 1)  # ±2% idiosyncratic
        base_wage = mpl * labor_share * (1 + tightness_adjustment) * noise
        
        # Floor: never post below 10% of the market average (prevents collapse)
        self.state.posted_wage_human = max(0.1 * market_wage_human, base_wage)
        
        # AI cost decreases with accumulated R&D (diminishing returns, floor at 20% of base)
        base_ai_cost = self.config.ai_wage_ratio
        r_and_d_effect = self.state.accumulated_r_and_d * self.config.r_and_d_efficiency
        max_reduction = 0.8  # R&D can reduce AI cost by at most 80%
        reduction = max_reduction * (1.0 - np.exp(-r_and_d_effect))
        self.state.posted_cost_ai = base_ai_cost * (1.0 - reduction)
    
    def hire_workers(self, matched_human: int, matched_ai: int) -> None:
        """Update employment based on matched workers.
        
        Separations are handled in worker.step() and reconciled in
        engine._reconcile_firm_headcounts(). This method only adds
        newly matched workers.
        
        Args:
            matched_human: Number of human workers matched to this firm
            matched_ai: Number of AI units matched to this firm
        """
        # Only add new hires — separations handled via worker.step() + reconciliation
        self.state.human_workers_employed += matched_human
        self.state.ai_workers_employed += matched_ai
    
    def produce_output(self) -> float:
        """Produce output given current workforce.
        
        Uses additive production: Y = A * (L_H + multiplier * L_AI)
        where A = firm productivity and multiplier = AI productivity relative to human.
        
        Returns:
            Output quantity produced
        """
        # Base productivity
        productivity = self.productivity_draw * self.state.human_productivity
        
        # Effective labor: human workers + AI-equivalent workers
        # Use config base multiplier + any R&D bonus accumulated in state
        ai_effective_units = self.state.ai_workers_employed * self.state.ai_productivity
        human_units = self.state.human_workers_employed
        
        output = productivity * (human_units + ai_effective_units)
        
        self.state.output_produced = max(0.0, output)
        return self.state.output_produced
    
    def compute_profits(self, output_price: float) -> float:
        """Compute profit for the period.
        
        Profit = Revenue - Labor Costs
        Revenue = output_price × output_produced
        Labor costs = wage_human × human_employed + cost_ai × ai_employed
        
        Args:
            output_price: Price per unit of output
            
        Returns:
            Profit (or loss if negative)
        """
        revenue = output_price * self.state.output_produced
        labor_costs = (self.state.posted_wage_human * self.state.human_workers_employed +
                      self.state.posted_cost_ai * self.state.ai_workers_employed)
        
        profit = revenue - labor_costs
        self.state.revenue = revenue
        self.state.profits = profit
        
        # Track loss streak for exit condition
        if profit < 0:
            self.state.losses_consecutive += 1
        else:
            self.state.losses_consecutive = 0
        
        # Accumulate capital
        self.state.capital += profit
        
        return profit
    
    def calculate_r_and_d_output(self, r_and_d_spending: float, current_period: int) -> tuple:
        """Calculate R&D output given current investment with heterogeneous efficiency.
        
        R&D spending creates two effects:
        1. AI cost reduction (40% of benefit)
        2. AI productivity boost (60% of benefit)
        
        Args:
            r_and_d_spending: R&D allocation this period
            current_period: Current simulation period
            
        Returns:
            (ai_cost_reduction, ai_productivity_boost) - amount and sign
        """
        if r_and_d_spending <= 0:
            return 0.0, 0.0
        
        # Apply firm-specific efficiency
        base_output = self.state.r_and_d_efficiency * r_and_d_spending
        
        # Random shock to innovation success
        r_and_d_shock = np.random.normal(1.0, 0.1)
        total_output = base_output * r_and_d_shock
        
        # Split between AI cost and productivity based on AI employment share
        total_employed = max(1, self.state.human_workers_employed + self.state.ai_workers_employed)
        ai_share = self.state.ai_workers_employed / total_employed
        
        # More R&D on AI reduction if high AI employment
        ai_cost_fraction = min(0.6, 0.3 + 0.3 * ai_share)  # 0.3-0.6
        prod_fraction = 1.0 - ai_cost_fraction
        
        ai_cost_reduction = ai_cost_fraction * total_output
        ai_productivity_boost = prod_fraction * total_output
        
        logger.debug(
            f"Firm {self.agent_id}: R&D output ({total_output:.3f}) "
            f"-> AI cost reduction ({ai_cost_reduction:.3f}), "
            f"AI productivity ({ai_productivity_boost:.3f})"
        )
        
        return ai_cost_reduction, ai_productivity_boost
    
    def apply_lagged_r_and_d_benefits(self, current_period: int) -> None:
        """Apply R&D benefits that have completed their lag period.
        
        R&D spending in period t realizes benefits in period t+lag_periods.
        
        Args:
            current_period: Current simulation period
        """
        lag_periods = getattr(self.config, 'r_and_d_lag_periods', 2)
        
        # Check pipeline for benefits realizing this period
        benefits_to_remove = []
        for idx, benefit in enumerate(self.state.r_and_d_pipeline):
            if benefit['realization_period'] == current_period:
                ai_cost_reduction, ai_productivity_boost = benefit['output']
                
                # Apply productivity boost (capped to prevent runaway growth)
                base_ai_prod = self.config.ai_productivity_multiplier
                max_ai_prod = base_ai_prod * 3.0  # Cap at 3× the base
                boost = 0.01 * ai_productivity_boost
                self.state.ai_productivity = min(max_ai_prod, self.state.ai_productivity + boost)
                
                logger.debug(
                    f"Firm {self.agent_id}: Lagged R&D benefit realized in period {current_period}: "
                    f"AI productivity += {0.01 * ai_productivity_boost:.4f}"
                )
                
                benefits_to_remove.append(idx)
        
        # Remove applied benefits (iterate backward to maintain indices)
        for idx in reversed(benefits_to_remove):
            self.state.r_and_d_pipeline.pop(idx)
    
    def make_r_and_d_decision(self, current_period: int = 0) -> None:
        """Decide R&D spending and queue benefits with lag.
        
        R&D dynamics (Phase 4):
        - Firm allocates r_and_d_profit_share of profits to R&D
        - R&D output calculated immediately with firm-specific efficiency
        - Benefits realized with lag (default: 2 periods)
        - Spillovers applied at economy level
        
        Args:
            current_period: Current simulation period (for lag calculation)
        """
        lag_periods = getattr(self.config, 'r_and_d_lag_periods', 2)
        
        # Allocate share of profits (if positive) to R&D
        if self.state.profits > 0:
            r_and_d_spend = self.state.profits * self.config.r_and_d_profit_share
        else:
            r_and_d_spend = 0.0
        
        self.state.r_and_d_spending = r_and_d_spend
        self.state.accumulated_r_and_d += r_and_d_spend
        self.state.r_and_d_history[current_period] = r_and_d_spend
        
        # Calculate output immediately
        if r_and_d_spend > 0:
            ai_cost_reduction, ai_productivity_boost = self.calculate_r_and_d_output(
                r_and_d_spend,
                current_period
            )
            
            # Queue benefits for later realization
            benefit_dict = {
                'origin_period': current_period,
                'output': (ai_cost_reduction, ai_productivity_boost),
                'realization_period': current_period + lag_periods
            }
            self.state.r_and_d_pipeline.append(benefit_dict)
    
    def check_exit_condition(self) -> bool:
        """Check if firm should exit market.
        
        Exit conditions:
        - Cumulative losses exceed threshold
        - Negative capital (bankruptcy)
        - Too many consecutive loss periods
        
        Returns:
            True if firm exits, False otherwise
        """
        if self.state.losses_consecutive >= self.config.loss_periods_to_exit:
            return True
        
        if self.state.capital < -10000:  # Deep bankruptcy
            return True
        
        return False
    
    def get_state(self) -> Dict:
        """Return firm state for logging."""
        return {
            **super().get_state(),
            **self.state.__dict__,
        }
