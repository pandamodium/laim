"""Market mechanics module - matching function."""

import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def cobb_douglas_match(
    unemployment: int,
    vacancies: int,
    efficiency: float = 1.0,
    elasticity: float = 0.5
) -> int:
    """Cobb-Douglas matching function.
    
    Matches = efficiency * (unemployment^elasticity) * (vacancies^(1-elasticity))
    
    Args:
        unemployment: Number of unemployed workers
        vacancies: Number of job vacancies
        efficiency: Matching efficiency parameter (A in standard formulation)
        elasticity: Elasticity parameter (typically 0.5)
        
    Returns:
        Number of matches
    """
    if unemployment == 0 or vacancies == 0:
        return 0
    
    matches = efficiency * (unemployment ** elasticity) * (vacancies ** (1 - elasticity))
    return int(np.floor(matches))


def allocate_matches(
    matches: int,
    job_applications: list,
    firm_capacities: dict
) -> dict:
    """Allocate matched jobs to workers.
    
    Args:
        matches: Total number of matches from matching function
        job_applications: List of (worker_id, firm_id, wage_offered)
        firm_capacities: Dict of firm_id -> remaining vacancies
        
    Returns:
        Dict of worker_id -> (firm_id, wage)
    """
    # TODO: Implement allocation logic
    # Simple version: Random draw from applications, respecting capacities
    allocations = {}
    return allocations
