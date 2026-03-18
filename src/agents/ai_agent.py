"""AI agent pooling (simplified model)."""

import logging

logger = logging.getLogger(__name__)


class AIAgentPool:
    """Simplified pooled model of AI agents.
    
    Instead of modeling individual AI agents, we track:
    - Total AI units employed by each firm
    - Cost per unit (endogenous to R&D)
    - Productivity per unit
    
    This reduces computational burden while capturing key dynamics.
    """
    
    def __init__(self):
        """Initialize AI agent pool tracking."""
        self.firm_ai_employment = {}  # firm_id -> number of AI units
        self.firm_ai_cost = {}  # firm_id -> cost per unit
        self.ai_productivity = 1.5  # Global productivity level
    
    def allocate_ai(self, firm_id: int, quantity: int, cost_per_unit: float) -> None:
        """Allocate AI units to firm.
        
        Args:
            firm_id: Firm receiving AI agents
            quantity: Number of AI units
            cost_per_unit: Cost per unit
        """
        self.firm_ai_employment[firm_id] = quantity
        self.firm_ai_cost[firm_id] = cost_per_unit
    
    def get_ai_employment(self, firm_id: int) -> int:
        """Get AI employment for firm."""
        return self.firm_ai_employment.get(firm_id, 0)
    
    def get_ai_cost(self, firm_id: int) -> float:
        """Get AI cost per unit for firm."""
        return self.firm_ai_cost.get(firm_id, 0.5)
