"""Base agent class for all simulation agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class Agent(ABC):
    """Abstract base class for all agents (firms, workers, etc.)."""
    
    def __init__(self, agent_id: int, agent_type: str):
        """Initialize agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type label (e.g., 'firm', 'worker')
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.created_period = 0
    
    @abstractmethod
    def step(self, env: Any) -> None:
        """Execute agent behavior for one period.
        
        Args:
            env: Simulation environment/context
        """
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """Return agent state as dictionary for logging/analysis."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(id={self.agent_id})"
