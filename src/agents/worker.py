"""Worker agent class."""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import numpy as np

from .base import Agent
from src.config import SimulationConfig

logger = logging.getLogger(__name__)


class WorkerStatus(Enum):
    """Enumeration of worker employment statuses."""
    EMPLOYED = "employed"
    UNEMPLOYED = "unemployed"
    ENTREPRENEUR = "entrepreneur"


class SkillLevel(Enum):
    """Worker skill level (if heterogeneity enabled)."""
    LOW = "low"
    HIGH = "high"


@dataclass
class WorkerState:
    """Encapsulates worker state."""
    status: WorkerStatus = WorkerStatus.UNEMPLOYED
    skill_level: SkillLevel = SkillLevel.LOW
    current_firm: Optional[int] = None
    current_wage: float = 0.0
    unemployment_duration: int = 0
    accumulated_savings: float = 0.0
    reservation_wage: float = 0.0


class Worker(Agent):
    """Worker agent in labor market."""
    
    def __init__(
        self,
        worker_id: int,
        config: SimulationConfig,
        skill_level: SkillLevel = SkillLevel.LOW
    ):
        """Initialize worker.
        
        Args:
            worker_id: Unique worker identifier
            config: Simulation configuration
            skill_level: Worker skill level
        """
        super().__init__(agent_id=worker_id, agent_type="worker")
        self.config = config
        self.state = WorkerState(skill_level=skill_level)
    
    def step(self, env) -> None:
        """Execute one period of worker behavior.
        
        Sequence:
        1. If employed, may separate exogenously
        2. If unemployed, update spell
        3. All workers with savings consider entrepreneurship
        4. Employed workers accumulate savings
        
        Args:
            env: Simulation environment
        """
        # 1. Exogenous separation for employed workers
        if self.state.status == WorkerStatus.EMPLOYED and self.state.current_firm is not None:
            separation_prob = self.config.separation_rate_employed
            if np.random.random() < separation_prob:
                # Worker becomes unemployed — firm headcount reconciled in engine
                # Preserve current_wage as "last wage" so UI benefits are computed correctly
                self.state.status = WorkerStatus.UNEMPLOYED
                self.state.current_firm = None
                self.state.unemployment_duration = 0
        
        # 2. Update unemployment dynamics if unemployed
        if self.state.status == WorkerStatus.UNEMPLOYED:
            self.update_unemployment_spell()
        
        # 3. Consider entrepreneurship (both employed and unemployed)
        # Employed founders = "opportunity entrepreneurship" (Lazear 2005)
        # Unemployed founders = "necessity entrepreneurship"
        if self.state.status in (WorkerStatus.EMPLOYED, WorkerStatus.UNEMPLOYED):
            avg_profit = getattr(env, '_avg_firm_profit', 0.0) if env else 0.0
            self.consider_entrepreneurship(avg_profit=avg_profit)
        
        # 4. At employment: accumulate savings
        if self.state.status == WorkerStatus.EMPLOYED:
            self.state.accumulated_savings += self.state.current_wage * 0.1
    
    def receive_job_offer(self, firm_id: int, wage: float) -> bool:
        """Receive and evaluate job offer.
        
        Worker accepts offer if wage exceeds reservation wage.
        
        Args:
            firm_id: ID of firm offering job
            wage: Offered wage
            
        Returns:
            True if worker accepts offer, False otherwise
        """
        # Only unemployed workers actively search
        if self.state.status != WorkerStatus.UNEMPLOYED:
            return False
        
        # Accept if offered wage meets or exceeds reservation wage
        accepts = wage >= self.state.reservation_wage
        
        if accepts:
            self.state.status = WorkerStatus.EMPLOYED
            self.state.current_firm = firm_id
            self.state.current_wage = wage
            self.state.unemployment_duration = 0  # Reset spell
        
        return accepts
    
    def evaluate_poaching_offer(self, firm_id: int, wage: float) -> bool:
        """Evaluate an outside offer while currently employed (on-the-job search).
        
        Worker switches if the outside wage exceeds current wage by the
        poaching threshold. This creates competitive pressure for firms
        to raise wages as productivity grows.
        
        Args:
            firm_id: ID of poaching firm
            wage: Offered wage from outside firm
            
        Returns:
            True if worker switches, False otherwise
        """
        if self.state.status != WorkerStatus.EMPLOYED:
            return False
        
        threshold = getattr(self.config, 'poaching_wage_threshold', 0.05)
        
        # Switch if outside offer exceeds current wage by threshold
        if wage > self.state.current_wage * (1 + threshold):
            old_firm_id = self.state.current_firm
            self.state.current_firm = firm_id
            self.state.current_wage = wage
            return True
        
        return False
    
    def consider_entrepreneurship(self, avg_profit: float = 0.0) -> bool:
        """Consider starting a business.
        
        Two channels (following Lazear 2005, Hurst & Lusardi 2004):
        
        **Opportunity entrepreneurship** (employed workers):
          - Lower base rate (most people don't quit stable jobs)
          - Rate rises when market profits are high (opportunity signal)
          - High-skill workers more likely (jack-of-all-trades theory)
          - Creates stronger firms (85-115% of incumbent productivity)
        
        **Necessity entrepreneurship** (unemployed workers):
          - Higher base rate (push factor from joblessness)
          - NOT increasing with unemployment duration (long-term
            unemployed lose networks and confidence)
          - Creates weaker firms (60-90% of incumbent productivity)
        
        Both channels require minimum capital (savings threshold).
        
        Args:
            avg_profit: Average incumbent firm profit (opportunity signal)
            
        Returns:
            True if worker decides to found a business
        """
        # Must have sufficient capital
        if self.state.accumulated_savings < self.config.min_capital_to_start_firm:
            return False
        
        base_rate = self.config.base_entrepreneurship_rate  # Annual rate (e.g. 5%)
        
        if self.state.status == WorkerStatus.EMPLOYED:
            # Opportunity entrepreneurship: employed workers quit to start firms
            # Much lower rate than unemployed — most don't quit stable jobs
            # Empirical: ~0.3% of workforce starts firms/year (BLS)
            rate = base_rate * 0.15  # 0.75% annual → ~0.8 per 1000 workers/month
            
            # Opportunity signal: high market profits → more entry
            # Normalized so avg_profit=0 → no effect, positive → boost
            if avg_profit > 0:
                opportunity_boost = min(1.0, 0.02 * avg_profit)  # Up to 2× rate
                rate *= (1 + opportunity_boost)
            
        elif self.state.status == WorkerStatus.UNEMPLOYED:
            # Necessity entrepreneurship: push factor from unemployment
            rate = base_rate * self.config.entrepreneurship_unemployed_premium
            
            # Decay with long unemployment (lose networks, skills, confidence)
            # Peak at ~3 months unemployed, then declines
            if self.state.unemployment_duration > 3:
                decay = 0.95 ** (self.state.unemployment_duration - 3)
                rate *= max(0.2, decay)  # Floor at 20% of peak
        else:
            return False
        
        # High-skill workers are more entrepreneurial (Lazear's jack-of-all-trades)
        if self.state.skill_level == SkillLevel.HIGH:
            rate *= 1.5
        
        # Clamp and convert annual rate to monthly
        rate = min(1.0, max(0.0, rate))
        monthly_rate = 1.0 - (1.0 - rate) ** (1.0 / 12.0)
        
        # Stochastic draw
        if np.random.random() < monthly_rate:
            self.state.status = WorkerStatus.ENTREPRENEUR
            self.state.accumulated_savings = 0  # Capital consumed
            return True
        
        return False
    
    def update_unemployment_spell(self) -> None:
        """Update unemployment duration, reservation wage, and savings.
        
        During unemployment:
        - Duration increases
        - Reservation wage decays over spell (search pressure)
        - Worker receives UI benefits (saved as wealth)
        """
        if self.state.status == WorkerStatus.UNEMPLOYED:
            self.state.unemployment_duration += 1
            
            # UI benefits (percentage of previous wage when last employed)
            ui_benefit = (self.state.current_wage * self.config.ui_replacement_rate 
                         if self.state.current_wage > 0 else 0.5)  # Default if never employed
            
            # Accumulate savings from UI
            self.state.accumulated_savings += ui_benefit
            
            # Reservation wage decays with unemployment duration (search pressure)
            # decay_factor = (0.95)^(unemployment_duration)
            decay_factor = 0.95 ** self.state.unemployment_duration
            self.state.reservation_wage = (ui_benefit * 
                                          self.config.reservation_wage_multiplier * 
                                          decay_factor)
    
    def get_state(self) -> Dict:
        """Return worker state for logging."""
        state_dict = self.state.__dict__.copy()
        # Convert enums to strings for storage
        state_dict["status"] = self.state.status.value
        state_dict["skill_level"] = self.state.skill_level.value
        
        return {
            **super().get_state(),
            **state_dict,
        }
