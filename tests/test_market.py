"""Test market mechanics."""

import pytest
import numpy as np
from src.market import cobb_douglas_match, phillips_curve_wage_adjustment


class TestMatching:
    """Tests for matching function."""
    
    def test_matching_basic(self):
        """Test basic matching function properties."""
        # No unemployment or vacancies -> no matches
        assert cobb_douglas_match(0, 100) == 0
        assert cobb_douglas_match(100, 0) == 0
        
        # Symmetric case
        matches = cobb_douglas_match(100, 100, efficiency=1.0, elasticity=0.5)
        assert isinstance(matches, int)
        assert matches > 0
        assert matches <= 100  # Can't exceed labor supply
    
    def test_matching_efficiency(self):
        """Test that matching efficiency increases matches."""
        matches_low = cobb_douglas_match(100, 100, efficiency=0.5)
        matches_high = cobb_douglas_match(100, 100, efficiency=2.0)
        
        assert matches_high > matches_low


class TestWageDynamics:
    """Tests for wage dynamics."""
    
    def test_phillips_curve_high_unemployment(self):
        """Test wages fall when unemployment is high."""
        wage_base = 1.0
        unemployment_high = 0.10  # 10% unemployment (above NAIRU)
        
        wage_new = phillips_curve_wage_adjustment(
            wage_base,
            unemployment_high,
            natural_unemployment_rate=0.045
        )
        
        # Should fall due to high unemployment
        assert wage_new < wage_base
    
    def test_phillips_curve_low_unemployment(self):
        """Test wages rise when unemployment is low."""
        wage_base = 1.0
        unemployment_low = 0.03  # 3% unemployment (below NAIRU)
        
        wage_new = phillips_curve_wage_adjustment(
            wage_base,
            unemployment_low,
            natural_unemployment_rate=0.045
        )
        
        # Should rise due to low unemployment
        assert wage_new > wage_base
