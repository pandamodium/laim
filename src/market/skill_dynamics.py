"""
Skill-Based Technical Change Module

Implements job categories, skill levels, and wage polarization dynamics.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SkillLevel(Enum):
    """Worker skill categories."""
    LOW = "low_skill"
    HIGH = "high_skill"


class JobCategory(Enum):
    """Job categories by AI exposure."""
    ROUTINE = "routine"  # High AI substitutability
    MANAGEMENT = "management"  # Medium AI substitutability  
    CREATIVE = "creative"  # Low AI substitutability


@dataclass
class JobCategoryProfile:
    """Profile of a job category."""
    category: JobCategory
    ai_productivity_multiplier: float  # AI output relative to human
    human_productivity: float  # Base human productivity
    wage_level: float  # Average wage relative to mean
    employment_share: float  # Fraction of total employment
    low_skill_concentration: float  # Fraction of low-skill workers in this category
    
    def get_ai_cost(self, base_ai_cost: float) -> float:
        """Compute AI cost in this category (adjusted for productivity)."""
        return base_ai_cost / self.ai_productivity_multiplier if self.ai_productivity_multiplier > 0 else float('inf')


class SkillHeterogeneoitModel:
    """Manages worker skill levels and job matching."""
    
    def __init__(self, config):
        """Initialize skill model from config."""
        self.config = config
        self.enabled = config.use_skill_heterogeneity
        self.low_skill_share = config.skill_distribution_low_share
        
        # Track employment by skill-category combination
        self.employment_matrix: Dict[tuple, int] = {}
        self.unemployment_by_skill: Dict[SkillLevel, int] = {
            SkillLevel.LOW: 0,
            SkillLevel.HIGH: 0
        }
        self.wages_by_skill: Dict[SkillLevel, float] = {
            SkillLevel.LOW: 1.0,
            SkillLevel.HIGH: 1.2
        }
    
    def assign_skill_level(self, random_draw: float) -> SkillLevel:
        """Assign skill level to worker based on random draw."""
        if not self.enabled:
            return SkillLevel.HIGH  # Default: everyone high-skill
        
        return SkillLevel.LOW if random_draw < self.low_skill_share else SkillLevel.HIGH
    
    def is_skill_match(self, worker_skill: SkillLevel, job_category: JobCategory) -> bool:
        """Check skill-job match quality."""
        if not self.enabled:
            return True
        
        # Soft matching: any skill can match any job, but with quality gradient
        if worker_skill == SkillLevel.HIGH:
            return True  # High-skill can do any job
        
        # Low-skill workers can do routine jobs better
        return job_category == JobCategory.ROUTINE
    
    def get_match_bonus(self, worker_skill: SkillLevel, job_category: JobCategory) -> float:
        """Get productivity bonus for skill-job match."""
        if not self.enabled:
            return 1.0
        
        if worker_skill == SkillLevel.HIGH:
            # High-skill gets bonuses in management and creative
            if job_category == JobCategory.CREATIVE:
                return 1.2
            elif job_category == JobCategory.MANAGEMENT:
                return 1.15
            else:  # routine
                return 0.9
        else:  # LOW-skill
            # Low-skill specialized in routine
            if job_category == JobCategory.ROUTINE:
                return 1.1
            elif job_category == JobCategory.MANAGEMENT:
                return 0.7
            else:  # creative
                return 0.6
    
    def update_wage_by_skill(self, low_skill_wage: float, high_skill_wage: float):
        """Update wage levels by skill."""
        self.wages_by_skill[SkillLevel.LOW] = low_skill_wage
        self.wages_by_skill[SkillLevel.HIGH] = high_skill_wage
    
    def get_wage_gap_ratio(self) -> float:
        """Calculate high-skill to low-skill wage ratio (inequality measure)."""
        low = self.wages_by_skill[SkillLevel.LOW]
        high = self.wages_by_skill[SkillLevel.HIGH]
        return high / low if low > 0 else 1.0
    
    def update_employment(self, low_skill_employed: int, high_skill_employed: int,
                         low_skill_unemployed: int, high_skill_unemployed: int):
        """Update employment counts by skill."""
        self.unemployment_by_skill[SkillLevel.LOW] = low_skill_unemployed
        self.unemployment_by_skill[SkillLevel.HIGH] = high_skill_unemployed
    
    def get_unemployment_rate_by_skill(self) -> Dict[SkillLevel, float]:
        """Calculate unemployment rate by skill level."""
        rates = {}
        for skill in [SkillLevel.LOW, SkillLevel.HIGH]:
            unemployed = self.unemployment_by_skill[skill]
            total = unemployed + round(1000 * (self.low_skill_share if skill == SkillLevel.LOW else 1 - self.low_skill_share))
            rates[skill] = unemployed / total if total > 0 else 0
        return rates
    
    def get_statistics(self) -> dict:
        """Return skill-based statistics."""
        wage_gap = self.get_wage_gap_ratio()
        unemployment_rates = self.get_unemployment_rate_by_skill()
        
        return {
            "wage_gap_ratio": wage_gap,
            "low_skill_unemployment": unemployment_rates[SkillLevel.LOW],
            "high_skill_unemployment": unemployment_rates[SkillLevel.HIGH],
            "low_skill_wage": self.wages_by_skill[SkillLevel.LOW],
            "high_skill_wage": self.wages_by_skill[SkillLevel.HIGH],
        }


class JobCategoryMarket:
    """Manages job categories and AI adoption by category."""
    
    def __init__(self, config):
        """Initialize job category market."""
        self.config = config
        self.enabled = config.use_job_categories
        
        # Initialize tracking before categories
        self.ai_adoption_by_category: Dict[JobCategory, float] = {}
        self.employment_by_category: Dict[JobCategory, Dict[str, int]] = {}
        
        # Define job categories with profiles
        self.categories: Dict[JobCategory, JobCategoryProfile] = {}
        self._initialize_categories()
    
    def _initialize_categories(self):
        """Create default job category profiles."""
        if not self.enabled:
            return
        
        multipliers = self.config.job_category_ai_multipliers
        
        # Routine jobs (high AI substitutable)
        self.categories[JobCategory.ROUTINE] = JobCategoryProfile(
            category=JobCategory.ROUTINE,
            ai_productivity_multiplier=multipliers.get("routine", 2.0),
            human_productivity=1.0,
            wage_level=0.9,
            employment_share=self.config.routine_job_share,
            low_skill_concentration=0.7
        )
        
        # Management jobs (low-medium AI substitutability)
        management_share = self.config.management_job_share
        self.categories[JobCategory.MANAGEMENT] = JobCategoryProfile(
            category=JobCategory.MANAGEMENT,
            ai_productivity_multiplier=multipliers.get("management", 0.5),
            human_productivity=1.2,
            wage_level=1.2,
            employment_share=management_share,
            low_skill_concentration=0.2
        )
        
        # Creative jobs (low AI substitutability)
        creative_share = 1.0 - self.config.routine_job_share - management_share
        self.categories[JobCategory.CREATIVE] = JobCategoryProfile(
            category=JobCategory.CREATIVE,
            ai_productivity_multiplier=multipliers.get("creative", 0.1),
            human_productivity=1.1,
            wage_level=1.1,
            employment_share=creative_share,
            low_skill_concentration=0.1
        )
        
        # Initialize adoption and employment tracking
        for category in self.categories.values():
            self.ai_adoption_by_category[category.category] = 0.0
            self.employment_by_category[category.category] = {
                "human": 0,
                "ai": 0
            }
    
    def get_category_for_job(self, job_type: Optional[str] = None) -> JobCategory:
        """Assign job to category (random if not specified)."""
        if not self.enabled or job_type is None:
            return JobCategory.ROUTINE
        
        if isinstance(job_type, str):
            try:
                return JobCategory[job_type.upper()]
            except KeyError:
                return JobCategory.ROUTINE
        
        return JobCategory.ROUTINE
    
    def get_ai_adoption_per_category(self) -> Dict[JobCategory, float]:
        """Get AI adoption rates by category."""
        if not self.enabled:
            return {JobCategory.ROUTINE: 0.1}
        
        return self.ai_adoption_by_category.copy()
    
    def update_ai_adoption(self, category: JobCategory, adoption_rate: float):
        """Update AI adoption in specific category."""
        if self.enabled and category in self.ai_adoption_by_category:
            current = self.ai_adoption_by_category[category]
            # Gradual adoption: adoption_rate is the rate of increase
            self.ai_adoption_by_category[category] = min(1.0, current + adoption_rate)
    
    def calculate_displacement(self, category: JobCategory, human_workers: int) -> int:
        """Calculate worker displacement in category due to AI adoption."""
        if not self.enabled:
            return 0
        
        adoption = self.ai_adoption_by_category.get(category, 0.0)
        # Displacement proportional to adoption rate
        displacement = int(human_workers * adoption)
        return min(displacement, human_workers)
    
    def get_ai_cost_in_category(self, category: JobCategory, base_ai_cost: float) -> float:
        """Get effective AI cost in specific job category."""
        if not self.enabled or category not in self.categories:
            return base_ai_cost
        
        profile = self.categories[category]
        return profile.get_ai_cost(base_ai_cost)
    
    def get_ai_productivity_in_category(self, category: JobCategory) -> float:
        """Get AI productivity relative to human in category."""
        if not self.enabled or category not in self.categories:
            return 1.5  # Default
        
        return self.categories[category].ai_productivity_multiplier
    
    def get_statistics(self) -> dict:
        """Return job category statistics."""
        if not self.enabled:
            return {}
        
        stats = {
            "ai_adoption_by_category": self.ai_adoption_by_category.copy(),
            "employment_by_category": {}
        }
        
        for category, employ_counts in self.employment_by_category.items():
            total = employ_counts["human"] + employ_counts["ai"]
            stats["employment_by_category"][category.value] = {
                "human": employ_counts["human"],
                "ai": employ_counts["ai"],
                "total": total,
                "ai_share": employ_counts["ai"] / total if total > 0 else 0.0
            }
        
        return stats


class WagePolarizationModel:
    """Models wage polarization as AI adoption differs across job categories."""
    
    def __init__(self, config, skill_model: SkillHeterogeneoitModel, 
                 job_market: JobCategoryMarket):
        """Initialize wage polarization model."""
        self.config = config
        self.skill_model = skill_model
        self.job_market = job_market
        
        self.wage_history: List[Dict] = []
    
    def calculate_wage_adjustment_for_category(self, category: JobCategory,
                                              current_wage: float,
                                              ai_adoption_rate: float,
                                              unemployment_rate: float) -> float:
        """Calculate wage adjustment due to AI adoption in category."""
        if not self.job_market.enabled:
            return current_wage
        
        # AI adoption reduces wage pressure in routine jobs, increases for creative
        adjustment_factor = 1.0
        
        if category == JobCategory.ROUTINE:
            # Routine jobs: displacement reduces wages
            adjustment_factor = 1.0 - (ai_adoption_rate * 0.1)  # Max -10% from AI
        elif category == JobCategory.CREATIVE:
            # Creative jobs: complement to AI increases wages  
            adjustment_factor = 1.0 + (ai_adoption_rate * 0.05)  # Max +5% from AI complement
        
        # Unemployment effect (Phillips curve)
        phillips_adjustment = 1.0 - (unemployment_rate * 0.5)
        
        return current_wage * adjustment_factor * phillips_adjustment
    
    def get_polarization_index(self) -> float:
        """Calculate wage polarization (high-to-low skill wage ratio)."""
        return self.skill_model.get_wage_gap_ratio()
    
    def record_wage_period(self, period: int, wages_by_category: Dict[JobCategory, float]):
        """Record wage levels for analysis."""
        self.wage_history.append({
            "period": period,
            "wages": wages_by_category.copy(),
            "polarization": self.get_polarization_index()
        })
    
    def get_statistics(self) -> dict:
        """Return wage polarization statistics."""
        if len(self.wage_history) < 2:
            return {"current_polarization": 1.0}
        
        current = self.wage_history[-1]["polarization"]
        previous = self.wage_history[-2]["polarization"] if len(self.wage_history) > 1 else current
        trend = current - previous
        
        return {
            "current_polarization": current,
            "polarization_trend": trend,
            "num_periods_tracked": len(self.wage_history)
        }
