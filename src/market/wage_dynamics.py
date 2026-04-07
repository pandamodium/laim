"""Wage dynamics module."""

import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def phillips_curve_wage_adjustment(
    current_wage: float,
    unemployment_rate: float,
    natural_unemployment_rate: float = 0.045,
    wage_adjustment_speed: float = 0.5,
    ai_employment_share: float = 0.1,
    downward_wage_rigidity: float = 0.3
) -> float:
    """Adjust wages using Phillips curve with asymmetric adjustment.
    
    **Wage gap = f(unemployment gap, AI share)**
    
    Phillips curve: wage_growth = -α*(u - u_n) - β*ai_share
    
    Downward wage rigidity: when wage_growth < 0, it is scaled by
    downward_wage_rigidity (0 = fully rigid, 1 = fully flexible).
    This captures the stylized fact that real wages fall slowly
    (inflation erodes them) rather than being cut directly.
    
    Args:
        current_wage: Current prevailing wage
        unemployment_rate: Current unemployment rate (0-1)
        natural_unemployment_rate: NAIRU (default 4.5%)
        wage_adjustment_speed: Speed of adjustment (lambda)
        ai_employment_share: Share of employment that is AI (dampens wages)
        downward_wage_rigidity: Fraction of upward speed at which wages fall
            (0 = fully rigid downward, 1 = symmetric/fully flexible)
        
    Returns:
        Next period wage
    """
    unemployment_gap = unemployment_rate - natural_unemployment_rate
    
    # Standard Phillips curve: lower unemployment → higher wage growth
    # Coefficient: 1% below NAIRU → ~0.5% wage growth
    wage_pressure = -1.0 * unemployment_gap  # Stronger Phillips curve coefficient
    
    # AI dampening: AI adoption suppresses wage growth
    ai_dampening = -0.1 * ai_employment_share  # Weaker dampening
    
    # Total wage change (scaled by adjustment speed)
    wage_growth = wage_adjustment_speed * (wage_pressure + ai_dampening)
    
    # Asymmetric adjustment: wages fall more slowly than they rise
    if wage_growth < 0:
        wage_growth *= downward_wage_rigidity
    
    return current_wage * (1 + wage_growth)


def compute_reservation_wage(
    ui_benefits: float,
    unemployment_duration: int,
    config
) -> float:
    """Compute worker reservation wage.
    
    Reservation wage depends on UI benefits and search duration.
    
    Args:
        ui_benefits: Unemployment insurance benefits
        unemployment_duration: How long unemployed (in periods)
        config: Simulation config
        
    Returns:
        Reservation wage
    """
    # Decay reservation wage over unemployment spell (search pressure)
    duration_decay = 0.95 ** unemployment_duration
    reservation_wage = config.reservation_wage_multiplier * ui_benefits * duration_decay
    return reservation_wage
