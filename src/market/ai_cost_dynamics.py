"""
AI Cost Dynamics Module

Implements endogenous AI cost curves with learning-by-doing effects.
"""

from dataclasses import dataclass, field
from typing import Dict, List
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class AICostTracker:
    """Tracks cumulative AI adoption and cost reductions."""
    base_ai_cost: float = 0.5
    cumulative_ai_adoption: float = 0.0  # Cumulative units deployed
    current_ai_cost: float = field(init=False)
    learning_parameter: float = 0.3  # λ in cost curve
    r_and_d_cost_reduction_rate: float = 0.002  # Per $1 R&D
    
    # History tracking
    cost_history: List[Dict] = field(default_factory=list)
    adoption_history: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        self.current_ai_cost = self.base_ai_cost
    
    def compute_ai_cost(self, cumulative_adoption: float) -> float:
        """
        Compute AI cost with learning curve.
        
        Cost = base_cost × (1 + adoption)^(-λ)
        
        This represents learning-by-doing as more AI is deployed.
        """
        if cumulative_adoption < 0:
            cumulative_adoption = 0
        
        # Cost reduction formula: cost decreases with adoption
        learning_factor = (1.0 + cumulative_adoption) ** (-self.learning_parameter)
        cost = self.base_ai_cost * learning_factor
        
        return cost
    
    def apply_r_and_d_benefit(self, r_and_d_spending: float) -> float:
        """
        Apply R&D-driven cost reduction per unit.
        
        Reduction per unit = r_and_d_spending / 1,000,000 × rate
        (Scaling down to per-unit basis)
        """
        # Scale R&D spending to per-unit cost reduction
        return (r_and_d_spending / 1_000_000) * self.r_and_d_cost_reduction_rate
    
    def update_adoption(self, ai_hired_this_period: int):
        """Update cumulative AI adoption."""
        self.cumulative_ai_adoption += ai_hired_this_period
        self.adoption_history.append(self.cumulative_ai_adoption)
    
    def apply_period(self, ai_hired_this_period: int, r_and_d_spending: float = 0.0):
        """
        Apply one period of AI cost dynamics.
        
        Updates adoption, computes new cost from learning curve and R&D.
        """
        # Step 1: Update cumulative adoption
        self.update_adoption(ai_hired_this_period)
        
        # Step 2: Compute cost from learning curve
        learning_cost = self.compute_ai_cost(self.cumulative_ai_adoption)
        
        # Step 3: Apply R&D cost reduction (per unit basis)
        r_and_d_reduction_per_unit = self.apply_r_and_d_benefit(r_and_d_spending)
        
        # Step 4: Final cost with both effects (reductions should be much smaller)
        self.current_ai_cost = max(0.01, learning_cost - r_and_d_reduction_per_unit)  # Floor at $0.01
        
        # Step 5: Record history
        self.cost_history.append({
            "current_cost": self.current_ai_cost,
            "learning_cost": learning_cost,
            "r_and_d_reduction": r_and_d_reduction_per_unit,
            "cumulative_adoption": self.cumulative_ai_adoption,
            "ai_hired": ai_hired_this_period,
            "r_and_d_spending": r_and_d_spending
        })
    
    def get_cost(self) -> float:
        """Get current AI cost."""
        return self.current_ai_cost
    
    def get_cost_reduction_from_baseline(self) -> float:
        """Get total cost reduction from baseline ($ and %)."""
        reduction_dollars = self.base_ai_cost - self.current_ai_cost
        reduction_pct = (reduction_dollars / self.base_ai_cost) if self.base_ai_cost > 0 else 0
        return reduction_dollars, reduction_pct
    
    def get_statistics(self) -> dict:
        """Return cost dynamics statistics."""
        reduction_dollars, reduction_pct = self.get_cost_reduction_from_baseline()
        
        return {
            "current_ai_cost": self.current_ai_cost,
            "base_ai_cost": self.base_ai_cost,
            "cost_reduction_dollars": reduction_dollars,
            "cost_reduction_percent": reduction_pct,
            "cumulative_ai_adopted": self.cumulative_ai_adoption,
            "periods_tracked": len(self.cost_history)
        }


class AIProductivityBoost:
    """Tracks AI productivity improvements from cumulative deployment."""
    
    def __init__(self, base_productivity: float = 1.5, learning_rate: float = 0.05):
        """
        Initialize AI productivity tracking.
        
        Args:
            base_productivity: Initial AI productivity relative to human (1.5x)
            learning_rate: Rate at which productivity improves with experience
        """
        self.base_productivity = base_productivity
        self.current_productivity = base_productivity
        self.learning_rate = learning_rate
        self.cumulative_ai_deployed = 0.0
        
        self.history: List[Dict] = []
    
    def apply_period(self, ai_employed_this_period: int, r_and_d_productivity_boost: float = 0.0):
        """
        Update AI productivity from cumulative deployment and R&D.
        
        Productivity improvements from:
        1. Learning-by-doing (minor effect)
        2. R&D investments (major effect)
        """
        # Update cumulative deployment
        self.cumulative_ai_deployed += ai_employed_this_period
        
        # Learning-by-doing: small improvements from experience
        learning_boost = self.learning_rate * (self.cumulative_ai_deployed / 1000)  # Scale to population
        
        # Apply both effects
        self.current_productivity = self.base_productivity + learning_boost + r_and_d_productivity_boost
        
        # Record history
        self.history.append({
            "current_productivity": self.current_productivity,
            "learning_boost": learning_boost,
            "r_and_d_boost": r_and_d_productivity_boost,
            "cumulative_deployed": self.cumulative_ai_deployed
        })
    
    def get_productivity_multiplier(self) -> float:
        """Get current AI productivity multiplier."""
        return self.current_productivity
    
    def get_statistics(self) -> dict:
        """Return productivity statistics."""
        return {
            "current_productivity": self.current_productivity,
            "base_productivity": self.base_productivity,
            "improvement_from_baseline": self.current_productivity - self.base_productivity,
            "cumulative_ai_deployed": self.cumulative_ai_deployed
        }


class MarketAIDynamics:
    """
    Manages market-level AI cost curves and dynamics.
    
    Represents economy-wide learning-by-doing and spillovers.
    """
    
    def __init__(self, config):
        """Initialize market AI dynamics."""
        self.config = config
        self.enabled = config.ai_cost_curve_learning_enabled
        
        # Initialize trackers
        self.cost_tracker = AICostTracker(
            base_ai_cost=config.ai_wage_ratio,
            learning_parameter=config.ai_cost_learning_parameter,
            r_and_d_cost_reduction_rate=config.r_and_d_ai_cost_rate
        )
        
        self.productivity_tracker = AIProductivityBoost(
            base_productivity=config.ai_productivity_multiplier,
            learning_rate=0.05
        )
        
        # Firm-level costs (can differ due to spillovers)
        self.firm_ai_costs: Dict[int, float] = {}
    
    def apply_period(self, total_ai_hired: int, total_r_and_d_spending: float):
        """
        Update market AI dynamics for one period.
        
        Args:
            total_ai_hired: Total AI units hired across all firms
            total_r_and_d_spending: Total R&D spending across all firms
        """
        if not self.enabled:
            return
        
        # Update market-level cost and productivity
        self.cost_tracker.apply_period(total_ai_hired, total_r_and_d_spending)
        
        # Compute derived productivity boost from R&D spillovers
        r_and_d_productivity_effect = (total_r_and_d_spending / 100000) * 0.1  # Calibrated effect
        self.productivity_tracker.apply_period(total_ai_hired, r_and_d_productivity_effect)
    
    def get_ai_cost_for_firm(self, firm_id: int) -> float:
        """Get AI cost for specific firm (with spillovers)."""
        if not self.enabled:
            return self.config.ai_wage_ratio
        
        # All firms benefit equally from market-level cost reductions
        return self.cost_tracker.get_cost()
    
    def get_ai_productivity_for_firm(self, firm_id: int) -> float:
        """Get AI productivity multiplier for firm."""
        if not self.enabled:
            return self.config.ai_productivity_multiplier
        
        # All firms benefit from productivity improvements
        return self.productivity_tracker.get_productivity_multiplier()
    
    def set_firm_ai_cost(self, firm_id: int, cost: float):
        """Override AI cost for specific firm."""
        self.firm_ai_costs[firm_id] = cost
    
    def get_elasticity_to_adoption(self) -> float:
        """
        Get elasticity of AI cost to adoption.
        
        This measures how responsive costs are to changes in adoption.
        Returns: -λ (negative, since cost decreases with adoption)
        """
        return -self.cost_tracker.learning_parameter
    
    def get_statistics(self) -> dict:
        """Return comprehensive AI dynamics statistics."""
        return {
            "cost_dynamics": self.cost_tracker.get_statistics(),
            "productivity_dynamics": self.productivity_tracker.get_statistics(),
            "elasticity_to_adoption": self.get_elasticity_to_adoption()
        }


class CostCurveAnalyzer:
    """
    Analyzes AI cost curve properties and implications.
    """
    
    @staticmethod
    def cost_elasticity_to_adoption(base_cost: float, cumulative_adoption: float, 
                                    learning_param: float) -> float:
        """
        Calculate elasticity of cost to adoption.
        
        ε = d(cost)/d(adoption) × adoption/cost
        
        For exponential form: ε = -λ (constant)
        """
        return -learning_param
    
    @staticmethod
    def time_to_cost_reduction(base_cost: float, learning_param: float, 
                               target_reduction_pct: float) -> int:
        """
        Estimate periods needed to achieve target cost reduction via learning.
        
        Args:
            target_reduction_pct: Target reduction (e.g., 0.25 for 25%)
        
        Returns:
            Approximate periods needed (assuming constant adoption rate)
        """
        target_cost = base_cost * (1 - target_reduction_pct)
        
        # Solve for adoption: cost = base × (1 + adoption)^(-λ)
        # target = base × (1 + adoption)^(-λ)
        # (target/base) = (1 + adoption)^(-λ)
        # Log both sides...
        
        ratio = target_cost / base_cost
        if ratio <= 0 or learning_param == 0:
            return float('inf')
        
        adoption_needed = (ratio ** (-1/learning_param)) - 1
        
        return max(1, int(adoption_needed))
    
    @staticmethod
    def cost_breakeven_analysis(human_wage: float, ai_cost: float,
                                ai_productivity: float) -> dict:
        """
        Analyze cost comparison between human and AI labor.
        
        Returns:
            dict with cost metrics
        """
        human_cost_per_unit = human_wage / 1.0  # Normalize human at 1.0 productivity
        ai_cost_per_unit = ai_cost / ai_productivity
        
        breakeven_wage = ai_cost / ai_productivity  # Human wage that equals AI cost-effectiveness
        
        return {
            "human_cost_per_unit_output": human_cost_per_unit,
            "ai_cost_per_unit_output": ai_cost_per_unit,
            "cost_advantage_for_ai": human_cost_per_unit > ai_cost_per_unit,
            "breakeven_human_wage": breakeven_wage,
            "ai_cost_advantage_pct": ((human_cost_per_unit - ai_cost_per_unit) / 
                                      human_cost_per_unit * 100)
        }
