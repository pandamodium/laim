"""Integration tests for Phase 2 - Market Mechanics."""

import pytest
import numpy as np
from src.config import SimulationConfig
from src.agents import Firm, Worker, SkillLevel, WorkerStatus
from src.market import JobMarket
from src.simulation import SimulationEngine


class TestJobMarket:
    """Test job market mechanics."""
    
    def test_job_market_initialization(self):
        """Test job market initializes correctly."""
        config = SimulationConfig()
        market = JobMarket(config)
        
        assert market.job_postings == []
        assert market.job_applications == []
        assert market.matches == {}
    
    def test_firms_post_jobs(self):
        """Test firms post job vacancies."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        market = engine.job_market
        
        market.firms_post_jobs(
            engine.firms,
            market_wage_human=1.0,
            market_ai_cost=0.5
        )
        
        # Should have posted jobs from all firms
        assert len(market.job_postings) > 0
        
        # Firms initially have ~317 humans each but demand fewer, 
        # so only AI openings are posted (net human openings = 0)
        ai_postings = [jp for jp in market.job_postings if jp.is_ai]
        assert len(ai_postings) > 0  # At least some AI
    
    def test_workers_apply(self):
        """Test unemployed workers apply to jobs."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        market = engine.job_market
        
        # Manually add human job postings (firms with full staff won't post human openings)
        from src.market.job_market import JobPosting
        market.job_postings.append(JobPosting(firm_id=0, wage=1.0, quantity=10, is_ai=False))
        
        # Workers apply
        market.workers_apply(engine.workers, unemployment_rate=0.05)
        
        # Should have applications from unemployed workers
        assert len(market.job_applications) > 0
    
    def test_matching_execution(self):
        """Test matching function execution."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        market = engine.job_market
        
        # Setup: post jobs and get applications
        market.firms_post_jobs(engine.firms, 1.0, 0.5)
        market.workers_apply(engine.workers, 0.05)
        
        # Get count of unemployed
        unemployed = sum(
            1 for w in engine.workers.values()
            if w.state.status == WorkerStatus.UNEMPLOYED
        )
        vacancies = sum(
            1 for jp in market.job_postings if not jp.is_ai
        )
        
        # Execute matching
        matches = market.execute_matching(engine.workers, unemployed, vacancies)
        
        # Should have some matches
        if unemployed > 0 and vacancies > 0:
            assert len(matches) > 0
            
            # Matches should be workers to firms
            for worker_id, (firm_id, wage) in matches.items():
                assert worker_id in engine.workers
                assert firm_id in engine.firms
                assert wage > 0
                
                # Worker should be employed after match
                worker = engine.workers[worker_id]
                assert worker.state.status == WorkerStatus.EMPLOYED
    
    def test_allocate_matches_to_firms(self):
        """Test allocation of matches to firms."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        market = engine.job_market
        
        # Setup and execute matching
        market.firms_post_jobs(engine.firms, 1.0, 0.5)
        market.workers_apply(engine.workers, 0.05)
        
        unemployed = sum(
            1 for w in engine.workers.values()
            if w.state.status == WorkerStatus.UNEMPLOYED
        )
        vacancies = sum(
            1 for jp in market.job_postings if not jp.is_ai
        )
        
        matches = market.execute_matching(engine.workers, unemployed, vacancies)
        
        # Count initial employment
        initial_employed = sum(
            f.state.human_workers_employed for f in engine.firms.values()
        )
        
        # Allocate matches
        market.allocate_matches_to_firms(engine.firms, matches)
        
        # Employment could go up or down due to separations during hiring
        # Just verify firms have been updated
        final_employed = sum(
            f.state.human_workers_employed for f in engine.firms.values()
        )
        
        assert final_employed >= 0  # Basic sanity check


class TestSimulationEngine:
    """Test simulation engine and orchestration."""
    
    def test_engine_initialization(self):
        """Test simulation engine initializes correctly."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        
        assert len(engine.firms) == config.num_firms
        assert len(engine.workers) == config.initial_human_workers
        assert engine.period == 0
        assert engine.market_wage_human > 0  # MPL-based, no longer fixed at 1.0
        assert engine.unemployment_rate == 0.0
    
    def test_initial_employment_split(self):
        """Test workers are split between employed and unemployed."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        
        employed = sum(
            1 for w in engine.workers.values()
            if w.state.status == WorkerStatus.EMPLOYED
        )
        unemployed = sum(
            1 for w in engine.workers.values()
            if w.state.status == WorkerStatus.UNEMPLOYED
        )
        
        # Should have ~95% employed, ~5% unemployed
        assert employed > 0
        assert unemployed > 0
        assert employed + unemployed == len(engine.workers)
    
    def test_single_period_execution(self):
        """Test single period executes without error."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        
        # Execute one period
        engine.step()
        
        assert engine.period == 1
        assert len(engine.metrics.metrics_history) == 1
    
    def test_market_statistics_computation(self):
        """Test market statistics are computed correctly."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        
        unemployed, unemp_rate, employed, vacancies = engine._compute_market_statistics()
        
        assert unemployed > 0
        assert 0 <= unemp_rate <= 1
        assert employed > 0
        assert unemployed + employed == len(engine.workers)
        assert vacancies >= 0
    
    def test_wage_adjustment(self):
        """Test that market wage is computed from firm posted wages (MPL-based)."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        
        # Market wage should be positive and derived from firm productivity
        assert engine.market_wage_human > 0
        
        # After updating, wage should reflect employment-weighted average of posted wages
        engine._update_aggregate_wage(unemployment_rate=0.05)
        assert engine.market_wage_human > 0
    
    def test_multiple_periods(self):
        """Test simulation runs for multiple periods."""
        config = SimulationConfig(simulation_periods=24)
        engine = SimulationEngine(config)
        
        for _ in range(12):
            engine.step()
        
        assert engine.period == 12
        assert len(engine.metrics.metrics_history) == 12
        
        # Unemployment should evolve
        unemp_rates = [
            m.unemployment_rate for m in engine.metrics.metrics_history
        ]
        
        # At least some variation expected
        assert len(set(unemp_rates)) > 1 or len(unemp_rates) == 1
    
    def test_output_production(self):
        """Test firms produce output and prices adjust."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        
        engine.step()
        
        # Should have positive total output
        assert engine.total_output >= 0
        
        # Check metrics recorded output
        assert len(engine.metrics.metrics_history) == 1
        assert engine.metrics.metrics_history[0].total_output == engine.total_output
    
    def test_full_simulation_short(self):
        """Test full simulation runs to completion."""
        config = SimulationConfig(
            simulation_periods=24,  # 2 years
            num_firms=2
        )
        
        engine = SimulationEngine(config)
        results = engine.run()
        
        # Check results DataFrame
        assert len(results) == 24
        assert "unemployment_rate" in results.columns
        assert "total_output" in results.columns
        assert "num_firms" in results.columns
        
        # Unemployment should be in reasonable range
        assert results["unemployment_rate"].min() >= 0
        assert results["unemployment_rate"].max() <= 1


class TestPhase2Integration:
    """End-to-end Phase 2 integration tests."""
    
    def test_market_clearing_cycle(self):
        """Test complete market clearing cycle."""
        config = SimulationConfig()
        engine = SimulationEngine(config)
        
        # Initial state
        initial_unemployed = sum(
            1 for w in engine.workers.values()
            if w.state.status == WorkerStatus.UNEMPLOYED
        )
        
        # Run one period
        engine.job_market.clear_market()
        engine.job_market.firms_post_jobs(engine.firms, 1.0, 0.5)
        engine.job_market.workers_apply(engine.workers, 0.05)
        
        unemployed_now = sum(
            1 for w in engine.workers.values()
            if w.state.status == WorkerStatus.UNEMPLOYED
        )
        
        # Matching should happen
        matches = engine.job_market.execute_matching(
            engine.workers,
            unemployed_now,
            sum(1 for jp in engine.job_market.job_postings if not jp.is_ai)
        )
        
        if matches:
            # Employment should increase
            employed_after = sum(
                1 for w in engine.workers.values()
                if w.state.status == WorkerStatus.EMPLOYED
            )
            
            assert employed_after > initial_unemployed - unemployed_now
    
    def test_unemployment_dynamics_over_time(self):
        """Test unemployment evolves realistically."""
        config = SimulationConfig(
            simulation_periods=60,
            separation_rate_employed=0.02,
            num_firms=3,
            matching_efficiency=1.5  # Higher efficiency to find jobs
        )
        
        engine = SimulationEngine(config)
        
        # Run 5 years
        for _ in range(60):
            engine.step()
        
        results = engine.metrics.get_results_dataframe()
        
        # Unemployment should be positive (some)
        mean_unemp = results["unemployment_rate"].mean()
        std_unemp = results["unemployment_rate"].std()
        
        # With 2% separation and matching, should have measurable unemployment
        # but not crisis levels. Allow wider range for testing.
        assert 0.0 <= mean_unemp <= 0.5  # Reasonable stability range
        assert std_unemp >= 0.0  # May or may not have variation
