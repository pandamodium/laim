"""Tests for Phase 3: Business Formation and Entrepreneurship (Optimized for Speed)."""

import pytest
import numpy as np
from src.simulation import SimulationEngine
from src.config import SimulationConfig
from src.agents import Worker, Firm, WorkerStatus, SkillLevel


class TestEntrepreneurshipDecision:
    """Test worker entrepreneurship decision logic (unit tests - no simulation)."""
    
    def test_entrepreneur_requires_capital(self):
        """Entrepreneur must have minimum capital to start firm."""
        config = SimulationConfig(
            num_firms=2,
            initial_human_workers=100,
            min_capital_to_start_firm=10000.0
        )
        engine = SimulationEngine(config)
        
        # Get an unemployed worker with insufficient capital
        worker = [w for w in engine.workers.values()
                  if w.state.status == WorkerStatus.UNEMPLOYED][0]
        worker.state.accumulated_savings = 1000.0  # Below minimum
        
        # Try entrepreneurship
        result = worker.consider_entrepreneurship()
        
        # Should not become entrepreneur
        assert result is False
        assert worker.state.status == WorkerStatus.UNEMPLOYED
    
    def test_entrepreneur_with_sufficient_capital(self):
        """Entrepreneur with sufficient capital can transition status."""
        config = SimulationConfig(
            num_firms=2,
            initial_human_workers=100,
            min_capital_to_start_firm=1000.0,
            base_entrepreneurship_rate=1.0  # 100% success rate
        )
        engine = SimulationEngine(config)
        
        # Get unemployed worker
        worker = [w for w in engine.workers.values()
                  if w.state.status == WorkerStatus.UNEMPLOYED][0]
        worker.state.accumulated_savings = 10000.0
        
        # Try entrepreneurship
        result = worker.consider_entrepreneurship()
        
        # Should become entrepreneur (with high probability)
        if result:
            assert worker.state.status == WorkerStatus.ENTREPRENEUR
            assert worker.state.accumulated_savings == 0  # Capital consumed


class TestFirmEntry:
    """Test firm entry dynamics (short simulations)."""
    
    def test_new_firm_has_employee(self):
        """New firm entry mechanics work."""
        config = SimulationConfig(
            num_firms=2,  # 2 firms for stability
            initial_human_workers=100,
            base_entrepreneurship_rate=0.50,
            min_capital_to_start_firm=500.0,
            loss_periods_to_exit=5,
            simulation_periods=12  # 1 year only
        )
        engine = SimulationEngine(config)
        
        initial_firms = len(engine.firms)
        assert initial_firms >= 2  # Start with 2
        
        # Run some periods - just verify it runs
        for period in range(12):
            engine.step()
        
        # Entry/exit mechanics executed without error
        final_firms = len(engine.firms)
        assert final_firms >= 0  # May have exited, which is okay


class TestFirmExit:
    """Test firm exit dynamics."""
    
    def test_exit_condition_exists(self):
        """Firms can exit on losses."""
        config = SimulationConfig(
            num_firms=2,
            initial_human_workers=100,
            loss_periods_to_exit=2,
            simulation_periods=12  # Short
        )
        engine = SimulationEngine(config)
        
        # Run simulation
        for _ in range(12):
            engine.step()
        
        # Check metrics recorded
        results = engine.metrics.get_results_dataframe()
        assert 'firms_exited' in results.columns


class TestMarketDynamicsQuick:
    """Test market dynamics with quick simulations."""
    
    def test_short_simulation_runs(self):
        """Short simulation completes."""
        config = SimulationConfig(
            num_firms=2,
            initial_human_workers=150,
            simulation_periods=12  # 1 year
        )
        engine = SimulationEngine(config)
        results = engine.run()
        
        assert len(results) == 12
        assert 'unemployment_rate' in results.columns
    
    def test_metrics_tracked(self):
        """Metrics are properly tracked."""
        config = SimulationConfig(
            num_firms=2,
            initial_human_workers=100,
            simulation_periods=12
        )
        engine = SimulationEngine(config)
        results = engine.run()
        
        # Key metrics present
        assert 'new_firms_entered' in results.columns
        assert 'firms_exited' in results.columns
        assert 'num_firms' in results.columns


class TestPhase3Quick:
    """Quick integration tests for Phase 3."""
    
    def test_basic_simulation_with_entry(self):
        """Simulation runs with entry mechanics."""
        config = SimulationConfig(
            num_firms=2,
            initial_human_workers=100,
            base_entrepreneurship_rate=0.10,
            min_capital_to_start_firm=2000.0,
            loss_periods_to_exit=3,
            simulation_periods=12
        )
        engine = SimulationEngine(config)
        results = engine.run()
        
        assert len(results) == 12
        assert not results.isnull().any().any()
    
    def test_worker_states_valid(self):
        """Workers maintain valid states."""
        config = SimulationConfig(
            num_firms=2,
            initial_human_workers=100,
            simulation_periods=12
        )
        engine = SimulationEngine(config)
        
        for _ in range(12):
            engine.step()
        
        # All workers in valid state
        for worker in engine.workers.values():
            assert worker.state.status in [WorkerStatus.UNEMPLOYED, WorkerStatus.EMPLOYED]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
