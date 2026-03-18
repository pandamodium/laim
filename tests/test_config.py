"""Test configuration."""

import pytest
from src.config import SimulationConfig, create_custom_config


class TestConfiguration:
    """Tests for simulation configuration."""
    
    def test_default_config(self):
        """Test default configuration is valid."""
        config = SimulationConfig()
        
        assert config.num_firms == 3
        assert config.initial_human_workers == 1000
        assert config.simulation_periods == 240
        assert config.ai_productivity_multiplier == 1.5
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = create_custom_config(
            num_firms=5,
            initial_human_workers=2000
        )
        
        assert config.num_firms == 5
        assert config.initial_human_workers == 2000
        assert config.ai_productivity_multiplier == 1.5  # Default preserved
    
    def test_config_validation(self):
        """Test configuration validation."""
        with pytest.raises(ValueError):
            SimulationConfig(num_firms=0)  # Must be >= 1
        
        with pytest.raises(ValueError):
            SimulationConfig(num_firms=100)  # Must be <= 20
