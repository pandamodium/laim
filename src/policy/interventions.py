"""
Policy Interventions Module

Implements unemployment insurance, retraining programs, and wage subsidies.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class UIBenefit:
    """Unemployment Insurance benefit tracking."""
    worker_id: int
    start_period: int
    duration_periods: int
    benefit_amount: float
    status: str = "active"  # active, expired, claimed
    periods_remaining: int = field(init=False)
    
    def __post_init__(self):
        self.periods_remaining = self.duration_periods
    
    def apply_period(self):
        """Decrement periods remaining."""
        self.periods_remaining -= 1
        if self.periods_remaining <= 0:
            self.status = "expired"
    
    def is_active(self) -> bool:
        """Check if UI is currently active and available."""
        return self.status == "active" and self.periods_remaining > 0


@dataclass
class RetrainingProgram:
    """Retraining program enrollment."""
    worker_id: int
    start_period: int
    duration_periods: int
    cost: float
    success_rate: float
    productivity_boost: float
    status: str = "in_progress"  # in_progress, completed, graduated, failed
    periods_remaining: int = field(init=False)
    succeeded: bool = field(init=False)
    
    def __post_init__(self):
        self.periods_remaining = self.duration_periods
        self.succeeded = False
    
    def apply_period(self):
        """Decrement periods in program."""
        self.periods_remaining -= 1
        if self.periods_remaining <= 0:
            self.status = "completed"
    
    def complete_program(self, success: bool):
        """Mark program completion."""
        self.status = "graduated" if success else "failed"
        self.succeeded = success


class UIBenefitTracker:
    """Tracks unemployment insurance for all workers."""
    
    def __init__(self):
        self.active_benefits: Dict[int, UIBenefit] = {}
        self.expired_benefits: Dict[int, UIBenefit] = {}
        self.total_spent: float = 0.0
    
    def create_benefit(self, worker_id: int, start_period: int, duration: int, amount: float) -> UIBenefit:
        """Create new UI benefit for unemployed worker."""
        benefit = UIBenefit(
            worker_id=worker_id,
            start_period=start_period,
            duration_periods=duration,
            benefit_amount=amount
        )
        self.active_benefits[worker_id] = benefit
        return benefit
    
    def get_benefit(self, worker_id: int) -> Optional[UIBenefit]:
        """Retrieve active UI benefit for worker."""
        return self.active_benefits.get(worker_id)
    
    def apply_period(self):
        """Decrement all active benefits, expire when needed."""
        expired = []
        for worker_id, benefit in self.active_benefits.items():
            benefit.apply_period()
            if benefit.status == "expired":
                expired.append(worker_id)
        
        # Move expired to archive
        for worker_id in expired:
            benefit = self.active_benefits.pop(worker_id)
            self.expired_benefits[worker_id] = benefit
    
    def get_benefit_amount(self, worker_id: int) -> Optional[float]:
        """Get benefit amount if active."""
        benefit = self.get_benefit(worker_id)
        if benefit and benefit.is_active():
            return benefit.benefit_amount
        return None
    
    def record_spending(self, amount: float):
        """Record UI spending."""
        self.total_spent += amount
    
    def get_total_recipients(self) -> int:
        """Count workers currently receiving UI."""
        return len([b for b in self.active_benefits.values() if b.is_active()])
    
    def get_statistics(self) -> dict:
        """Return UI program statistics."""
        return {
            "active_recipients": self.get_total_recipients(),
            "total_spent": self.total_spent,
            "average_benefit": (
                self.total_spent / self.get_total_recipients() 
                if self.get_total_recipients() > 0 else 0.0
            )
        }


class RetrainingProgramTracker:
    """Tracks retraining program enrollment and completion."""
    
    def __init__(self):
        self.active_programs: Dict[int, RetrainingProgram] = {}
        self.completed_programs: Dict[int, RetrainingProgram] = {}
        self.total_cost: float = 0.0
        self.graduates_count: int = 0
    
    def enroll_worker(self, worker_id: int, start_period: int, duration: int, 
                     cost: float, success_rate: float, boost: float) -> RetrainingProgram:
        """Enroll worker in retraining program."""
        program = RetrainingProgram(
            worker_id=worker_id,
            start_period=start_period,
            duration_periods=duration,
            cost=cost,
            success_rate=success_rate,
            productivity_boost=boost
        )
        self.active_programs[worker_id] = program
        self.total_cost += cost
        return program
    
    def get_program(self, worker_id: int) -> Optional[RetrainingProgram]:
        """Get active retraining program for worker."""
        return self.active_programs.get(worker_id)
    
    def apply_period(self):
        """Update all programs by one period."""
        completed = []
        for worker_id, program in self.active_programs.items():
            program.apply_period()
            if program.status == "completed":
                completed.append(worker_id)
        
        # Move completed to archive
        for worker_id in completed:
            program = self.active_programs.pop(worker_id)
            self.completed_programs[worker_id] = program
    
    def graduate_worker(self, worker_id: int, success: bool):
        """Mark worker as graduating from program."""
        # Check active programs first
        program = self.get_program(worker_id)
        
        #If not active, check completed
        if not program:
            program = self.completed_programs.get(worker_id)
        
        # Mark status and count graduates
        if program:
            program.complete_program(success)
            if success:
                self.graduates_count += 1
    
    def get_program_boost(self, worker_id: int) -> float:
        """Get productivity boost for recently graduated worker."""
        # Check completed programs from most recent period
        program = self.completed_programs.get(worker_id)
        if program and program.succeeded:
            boost = program.productivity_boost
            # Remove from dict to avoid repeated boost
            del self.completed_programs[worker_id]
            return boost
        return 0.0
    
    def get_statistics(self) -> dict:
        """Return retraining program statistics."""
        total_completed = len(self.completed_programs)
        return {
            "active_enrollees": len(self.active_programs),
            "total_completed": total_completed,
            "total_graduates": self.graduates_count,
            "success_rate": (
                self.graduates_count / total_completed 
                if total_completed > 0 else 0.0
            ),
            "total_cost": self.total_cost
        }


class WageSubsidyTracker:
    """Tracks wage subsidies for eligible workers."""
    
    def __init__(self, enabled: bool, amount: float, target_group: str):
        self.enabled = enabled
        self.subsidy_amount = amount
        self.target_group = target_group  # 'displaced', 'low_skill', 'all'
        self.subsidized_workers: set = set()  # Workers currently receiving subsidy
        self.total_spent: float = 0.0
    
    def is_eligible(self, worker, target_worker_class) -> bool:
        """Check if worker is eligible for subsidy."""
        if not self.enabled or self.subsidy_amount <= 0:
            return False
        
        if self.target_group == "all":
            return True
        elif self.target_group == "displaced":
            return hasattr(worker, 'is_displaced') and worker.is_displaced
        elif self.target_group == "low_skill":
            return hasattr(worker, 'skill_level') and worker.skill_level == "low"
        
        return False
    
    def apply_subsidy(self, worker_id: int):
        """Apply subsidy to eligible worker."""
        if self.enabled and worker_id not in self.subsidized_workers:
            self.subsidized_workers.add(worker_id)
    
    def remove_subsidy(self, worker_id: int):
        """Remove subsidy from worker."""
        if worker_id in self.subsidized_workers:
            self.subsidized_workers.discard(worker_id)
    
    def get_subsidy_for_firm(self, firm_id: int, hired_this_period: list) -> float:
        """Calculate total subsidy for firm on new hires."""
        if not self.enabled:
            return 0.0
        
        subsidy = len(hired_this_period) * self.subsidy_amount
        self.total_spent += subsidy
        return subsidy
    
    def get_statistics(self) -> dict:
        """Return subsidy program statistics."""
        return {
            "active_recipients": len(self.subsidized_workers),
            "total_paid": self.total_spent,
            "average_subsidy": (
                self.total_spent / len(self.subsidized_workers)
                if len(self.subsidized_workers) > 0 else 0.0
            )
        }


class TaxCreditTracker:
    """Tracks R&D and hiring tax credits."""
    
    def __init__(self, r_and_d_enabled: bool = False, r_and_d_rate: float = 0.25,
                 hiring_enabled: bool = False, hiring_amount: float = 2000.0):
        self.r_and_d_enabled = r_and_d_enabled
        self.r_and_d_rate = r_and_d_rate
        self.hiring_enabled = hiring_enabled
        self.hiring_amount = hiring_amount
        
        self.r_and_d_credits: Dict[int, float] = {}  # firm_id -> credit amount
        self.hiring_credits: Dict[int, float] = {}   # firm_id -> credit amount
        
        self.total_r_and_d_spent: float = 0.0
        self.total_hiring_spent: float = 0.0
    
    def calculate_r_and_d_credit(self, r_and_d_spending: float) -> float:
        """Calculate R&D tax credit."""
        if not self.r_and_d_enabled:
            return 0.0
        return r_and_d_spending * self.r_and_d_rate
    
    def calculate_hiring_credit(self, net_hires: int) -> float:
        """Calculate hiring tax credit."""
        if not self.hiring_enabled or net_hires <= 0:
            return 0.0
        return net_hires * self.hiring_amount
    
    def apply_credits_to_firm(self, firm_id: int, r_and_d_spending: float, 
                             net_hires: int):
        """Apply credits to firm and track spending."""
        r_and_d_credit = self.calculate_r_and_d_credit(r_and_d_spending)
        hiring_credit = self.calculate_hiring_credit(net_hires)
        
        if r_and_d_credit > 0:
            self.r_and_d_credits[firm_id] = r_and_d_credit
            self.total_r_and_d_spent += r_and_d_credit
        
        if hiring_credit > 0:
            self.hiring_credits[firm_id] = hiring_credit
            self.total_hiring_spent += hiring_credit
    
    def get_credits(self, firm_id: int) -> tuple:
        """Get tax credits for firm (r_and_d, hiring)."""
        r_and_d = self.r_and_d_credits.pop(firm_id, 0.0)
        hiring = self.hiring_credits.pop(firm_id, 0.0)
        return r_and_d, hiring
    
    def get_statistics(self) -> dict:
        """Return tax credit program statistics."""
        return {
            "total_r_and_d_credits": self.total_r_and_d_spent,
            "total_hiring_credits": self.total_hiring_spent,
            "total_cost": self.total_r_and_d_spent + self.total_hiring_spent
        }


class PolicyModule:
    """Unified policy intervention module."""
    
    def __init__(self, config):
        """Initialize all policy systems based on config."""
        self.config = config
        
        # Initialize systems
        self.ui_tracker = UIBenefitTracker()
        self.retraining_tracker = RetrainingProgramTracker()
        self.subsidy_tracker = WageSubsidyTracker(
            enabled=config.wage_subsidy_enabled,
            amount=config.wage_subsidy_amount,
            target_group=config.wage_subsidy_target_group
        )
        self.tax_credit_tracker = TaxCreditTracker(
            r_and_d_enabled=config.r_and_d_tax_credit_enabled,
            r_and_d_rate=config.r_and_d_tax_credit_rate,
            hiring_enabled=config.hiring_tax_credit_enabled,
            hiring_amount=config.hiring_tax_credit_amount
        )
    
    def apply_period(self):
        """Update all policy systems for new period."""
        self.ui_tracker.apply_period()
        self.retraining_tracker.apply_period()
    
    def get_all_statistics(self) -> dict:
        """Get comprehensive policy statistics."""
        return {
            "ui": self.ui_tracker.get_statistics(),
            "retraining": self.retraining_tracker.get_statistics(),
            "subsidies": self.subsidy_tracker.get_statistics(),
            "tax_credits": self.tax_credit_tracker.get_statistics()
        }
