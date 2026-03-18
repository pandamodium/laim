"""Job market coordination and matching system."""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from src.market import cobb_douglas_match

logger = logging.getLogger(__name__)


@dataclass
class JobPosting:
    """A job posting by a firm."""
    firm_id: int
    wage: float
    quantity: int
    is_ai: bool = False


@dataclass
class JobApplication:
    """A worker application to a job."""
    worker_id: int
    firm_id: int
    wage: float
    is_ai: bool = False


class JobMarket:
    """Central job market that coordinates hiring between firms and workers."""
    
    def __init__(self, config):
        """Initialize job market.
        
        Args:
            config: SimulationConfig
        """
        self.config = config
        self.job_postings: List[JobPosting] = []
        self.job_applications: List[JobApplication] = []
        self.matches: Dict[int, Tuple[int, float]] = {}  # worker_id -> (firm_id, wage)
    
    def clear_market(self) -> None:
        """Clear market at start of each period."""
        self.job_postings = []
        self.job_applications = []
        self.matches = {}
    
    def firms_post_jobs(
        self,
        firms: Dict[int, 'Firm'],
        market_wage_human: float,
        market_ai_cost: float
    ) -> None:
        """Firms post job vacancies and wages.
        
        Args:
            firms: Dictionary of firm agents
            market_wage_human: Current market wage for humans
            market_ai_cost: Current market cost per AI unit
        """
        for firm_id, firm in firms.items():
            # Update firm's posted wages
            firm.post_wages_and_vacancies(market_wage_human)
            
            # Firm computes desired labor input
            output_target = 10 + firm_id * 5  # Simple: distribute across firms
            human_demand, ai_demand = firm.compute_labor_demand(
                firm.state.posted_wage_human,
                firm.state.posted_cost_ai,
                output_target
            )
            
            # Post human job openings
            if human_demand > 0:
                self.job_postings.append(
                    JobPosting(
                        firm_id=firm_id,
                        wage=firm.state.posted_wage_human,
                        quantity=human_demand,
                        is_ai=False
                    )
                )
            
            # Post AI "jobs" (really AI unit purchases)
            if ai_demand > 0:
                self.job_postings.append(
                    JobPosting(
                        firm_id=firm_id,
                        wage=firm.state.posted_cost_ai,
                        quantity=ai_demand,
                        is_ai=True
                    )
                )
            
            firm.state.job_openings_human = human_demand
            firm.state.job_openings_ai = ai_demand
    
    def workers_apply(
        self,
        workers: Dict[int, 'Worker'],
        unemployment_rate: float
    ) -> None:
        """Unemployed workers apply to posted jobs.
        
        Job application process:
        - Only unemployed workers apply
        - Each unemployed applies to 2-3 random postings
        - Accept/reject determined in matching phase
        
        Args:
            workers: Dictionary of worker agents
            unemployment_rate: Current unemployment rate (for statistics)
        """
        # Get unemployed workers
        unemployed = [
            (wid, w) for wid, w in workers.items()
            if w.state.status.value == 'unemployed'
        ]
        
        # Unemployed workers apply to random job postings
        for worker_id, worker in unemployed:
            if not self.job_postings:
                continue
            
            # Each worker applies to ~2 random positions
            num_applications = np.random.randint(1, 3)
            
            for _ in range(num_applications):
                posting = self.job_postings[np.random.randint(0, len(self.job_postings))]
                
                # Skip AI "jobs" - only humans apply
                if posting.is_ai:
                    continue
                
                self.job_applications.append(
                    JobApplication(
                        worker_id=worker_id,
                        firm_id=posting.firm_id,
                        wage=posting.wage,
                        is_ai=False
                    )
                )
    
    def execute_matching(
        self,
        workers: Dict[int, 'Worker'],
        unemployment_count: int,
        job_vacancy_count: int
    ) -> Dict[int, Tuple[int, float]]:
        """Execute matching function and allocate jobs.
        
        Matching process:
        1. Use Cobb-Douglas matching function to determine total matches
        2. Random allocation to workers who accept offers
        3. Return job allocations
        
        Args:
            workers: Dictionary of worker agents
            unemployment_count: Total unemployed workers
            job_vacancy_count: Total job vacancies posted
            
        Returns:
            Dictionary of worker_id -> (firm_id, wage) for accepted jobs
        """
        # Apply matching function
        matches_count = cobb_douglas_match(
            unemployment_count,
            job_vacancy_count,
            efficiency=self.config.matching_efficiency,
            elasticity=self.config.matching_elasticity
        )
        
        # Randomly sample applications to match
        if not self.job_applications or matches_count == 0:
            return {}
        
        matches_made = 0
        matched_workers = set()
        matches = {}
        
        # Randomly iterate through applications
        application_indices = np.random.permutation(len(self.job_applications))
        
        for idx in application_indices:
            if matches_made >= matches_count:
                break
            
            app = self.job_applications[idx]
            
            # Skip if worker already matched or not in workers dict
            if app.worker_id in matched_workers or app.worker_id not in workers:
                continue
            
            worker = workers[app.worker_id]
            
            # Worker evaluates offer
            if worker.receive_job_offer(app.firm_id, app.wage):
                matches[app.worker_id] = (app.firm_id, app.wage)
                matched_workers.add(app.worker_id)
                matches_made += 1
        
        self.matches = matches
        return matches
    
    def allocate_matches_to_firms(
        self,
        firms: Dict[int, 'Firm'],
        matches: Dict[int, Tuple[int, float]]
    ) -> None:
        """Allocate matched workers to firms and update employment.
        
        Args:
            firms: Dictionary of firm agents
            matches: Matches from execute_matching()
        """
        # Count matches by firm
        firm_matches = {}
        
        for worker_id, (firm_id, wage) in matches.items():
            if firm_id not in firm_matches:
                firm_matches[firm_id] = {"human": 0, "ai": 0}
            firm_matches[firm_id]["human"] += 1
        
        # Add AI "matches" (unlimited supply at cost)
        for posting in self.job_postings:
            if posting.is_ai:
                if posting.firm_id not in firm_matches:
                    firm_matches[posting.firm_id] = {"human": 0, "ai": 0}
                firm_matches[posting.firm_id]["ai"] += posting.quantity
        
        # Update firm employment
        for firm_id, firm in firms.items():
            matched = firm_matches.get(firm_id, {"human": 0, "ai": 0})
            firm.hire_workers(matched["human"], matched["ai"])
    
    def get_market_statistics(self) -> Dict:
        """Compute market-level statistics.
        
        Returns:
            Dictionary with market stats
        """
        return {
            "job_postings_count": len(self.job_postings),
            "job_applications_count": len(self.job_applications),
            "matches_count": len(self.matches),
            "human_vacancies": sum(
                1 for jp in self.job_postings if not jp.is_ai
            ),
            "human_applications": sum(
                1 for ja in self.job_applications if not ja.is_ai
            ),
        }
