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
    profits: float = 0.0
    losses_consecutive: int = 0
    capital: float = 0.0
    r_and_d_spending: float = 0.0
    accumulated_r_and_d: float = 0.0
    ai_productivity: float = 1.5
    human_productivity: float = 1.0


class Firm(Agent):
    """Oligopolistic firm agent in labor market."""
    
    def __init__(
        self,
        firm_id: int,
        config: SimulationConfig,
        initial_capital: float = 50000.0
    ):
        """Initialize firm.
        
        Args:
            firm_id: Unique firm identifier
            config: Simulation configuration
            initial_capital: Starting capital/wealth
        """
        super().__init__(agent_id=firm_id, agent_type="firm")
        self.config = config
        self.state = FirmState(capital=initial_capital)
        self.productivity_draw = np.random.normal(loc=1.0, scale=0.1)
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
        self.post_wages_and_vacancies(market_wage)
        
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
        """Compute optimal human and AI labor demand using CES production.
        
        CES Production Function:
            Y = A[αL_H^(-σ) + (1-α)L_AI^(-σ)]^(-1/σ)
        
        where:
        - σ = (elasticity - 1) / elasticity  (relates elasticity of substitution)
        - α = share parameter for human labor
        - A = firm productivity
        
        This function solves for cost-minimizing labor bundles.
        
        Args:
            wage_human: Wage per human worker
            cost_ai: Cost per AI unit
            output_target: Desired output level
            
        Returns:
            (human_workers_demanded, ai_workers_demanded)
        """
        if output_target <= 0 or wage_human <= 0 or cost_ai <= 0:
            return 0, 0
        
        # CES elasticity of substitution parameter
        # elasticity of 1.5 means sigma = 1/3 ≈ 0.333
        sigma = 1.0 / self.config.firm_substitution_elasticity
        
        # Solve for optimal labor demand using first-order conditions
        # From cost minimization: (L_H / L_AI) = [(w_H / w_AI) * ((1-α) / α)]^(σ)
        
        # Use α = 0.6 (60% weight to human, 40% to AI) as default
        alpha = 0.6
        
        # Cost ratio
        cost_ratio = wage_human / max(cost_ai, 0.01)  # Avoid div by zero
        
        # Optimal labor ratio using first-order conditions
        # This is derived from minimizing cost subject to CES production
        labor_ratio = ((1 - alpha) / alpha * cost_ratio) ** sigma
        
        # From production function: Y = A[α*L_H^(-σ) + (1-α)*L_AI^(-σ)]^(-1/σ)
        # Solve for L_H given L_AI = labor_ratio * L_H
        # After substitution and algebra:
        # L_H ≈ output_target / (A * [α^(-1/σ) + (1-α)^(-1/σ) * labor_ratio^(-1/σ)]^(-σ))
        
        # Simplified approximation for computational efficiency
        productivity_factor = self.productivity_draw * self.state.human_productivity
        
        # Demand based on output_target and relative prices
        if labor_ratio > 0:
            human_demand = output_target / (productivity_factor * 1.5 * (1 + labor_ratio))
            ai_demand = labor_ratio * human_demand
        else:
            human_demand = output_target / (productivity_factor * 1.5)
            ai_demand = 0
        
        return max(0, int(np.round(human_demand))), max(0, int(np.round(ai_demand)))
    
    def post_wages_and_vacancies(self, market_wage_human: float) -> None:
        """Post wages and job openings.
        
        Firm sets human wage as slight markup over market wage (wage competition).
        AI cost is determined by R&D productivity level.
        
        Args:
            market_wage_human: Prevailing market wage for comparison
        """
        # Wage markup strategy: post slightly above market to attract workers (or at market)
        wage_markup = 1.0 + 0.05 * np.random.normal(0, 1)  # ±5% random variation
        self.state.posted_wage_human = market_wage_human * max(0.9, wage_markup)
        
        # AI cost decreases with accumulated R&D
        base_ai_cost = self.config.ai_wage_ratio
        r_and_d_effect = self.state.accumulated_r_and_d * self.config.r_and_d_efficiency
        self.state.posted_cost_ai = base_ai_cost * np.exp(-r_and_d_effect)
    
    def hire_workers(self, matched_human: int, matched_ai: int) -> None:
        """Update employment based on matched workers.
        
        Args:
            matched_human: Number of human workers matched to this firm
            matched_ai: Number of AI units matched to this firm
        """
        # Exogenous separation of existing workforce
        separation_rate = self.config.separation_rate_employed
        humans_separated = int(np.random.binomial(self.state.human_workers_employed, separation_rate))
        ai_separated = int(np.random.binomial(self.state.ai_workers_employed, separation_rate))
        
        # Update employment
        self.state.human_workers_employed = max(0, self.state.human_workers_employed - humans_separated + matched_human)
        self.state.ai_workers_employed = max(0, self.state.ai_workers_employed - ai_separated + matched_ai)
    
    def produce_output(self) -> float:
        """Produce output given current workforce using CES production function.
        
        Output = A * [α*L_H^(-σ) + (1-α)*L_AI^(-σ)]^(-1/σ)
        
        where:
        - A = firm productivity
        - L_H = human workers
        - L_AI = AI units (adjusted for productivity)
        - σ = elasticity parameter
        - α = share parameter
        
        Returns:
            Output quantity produced
        """
        # Base productivity
        productivity = self.productivity_draw * self.state.human_productivity
        
        # AI productivity adjusted
        ai_effective_units = self.state.ai_workers_employed * self.state.ai_productivity
        human_units = self.state.human_workers_employed
        
        if human_units == 0 and ai_effective_units == 0:
            self.state.output_produced = 0.0
            return 0.0
        
        # CES aggregation with safe computation
        sigma = 1.0 / self.config.firm_substitution_elasticity
        alpha = 0.6  # Human labor share parameter
        
        # Handle edge cases: if one input is zero, use Leontief approximation
        if human_units == 0:
            output = productivity * ai_effective_units  # AI only
        elif ai_effective_units == 0:
            output = productivity * human_units  # Human only
        else:
            # Standard CES
            try:
                ces_term = (alpha * (human_units ** (-sigma)) + 
                           (1 - alpha) * (ai_effective_units ** (-sigma)))
                output = productivity * (ces_term ** (-1.0 / sigma))
            except (ZeroDivisionError, ValueError):
                # Fallback to Cobb-Douglas if CES has issues
                output = productivity * (human_units ** alpha) * (ai_effective_units ** (1 - alpha))
        
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
        self.state.profits = profit
        
        # Track loss streak for exit condition
        if profit < 0:
            self.state.losses_consecutive += 1
        else:
            self.state.losses_consecutive = 0
        
        # Accumulate capital
        self.state.capital += profit
        
        return profit
    
    def make_r_and_d_decision(self) -> None:
        """Decide R&D spending and update productivity.
        
        R&D dynamics:
        - Firm allocates r_and_d_profit_share of current profits to R&D
        - R&D spending reduces AI costs with lag
        - Productivity improvement follows stochastic process
        """
        # Allocate share of profits (if positive) to R&D
        if self.state.profits > 0:
            r_and_d_spend = self.state.profits * self.config.r_and_d_profit_share
        else:
            r_and_d_spend = 0.0
        
        self.state.r_and_d_spending = r_and_d_spend
        self.state.accumulated_r_and_d += r_and_d_spend
        
        # R&D increases AI productivity (with random shock)
        r_and_d_shock = np.random.normal(1.0, 0.1)  # ~10% std dev
        productivity_gain = self.config.r_and_d_efficiency * r_and_d_spend * r_and_d_shock
        self.state.ai_productivity += 0.01 * productivity_gain
    
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
