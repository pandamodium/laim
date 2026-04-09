"""Integration tests for Phase 1 - Core Agent Behavior."""

import pytest
import numpy as np
from src.config import SimulationConfig
from src.agents import Firm, Worker, SkillLevel, WorkerStatus


class TestFirmBehavior:
    """Test complete firm agent behavior over time."""
    
    def test_firm_labor_demand_calculation(self):
        """Test firm computes reasonable labor demand."""
        config = SimulationConfig()
        firm = Firm(firm_id=0, config=config)
        
        wage_human = 1.0
        cost_ai = 0.5
        output_target = 10.0
        
        human_demand, ai_demand = firm.compute_labor_demand(wage_human, cost_ai, output_target)
        
        # Demand should be non-negative
        assert human_demand >= 0
        assert ai_demand >= 0
        
        # With cheaper AI, should demand more AI
        human_demand_higher_ai_cost, ai_demand_higher_ai_cost = firm.compute_labor_demand(
            wage_human, 1.0, output_target
        )
        assert ai_demand > ai_demand_higher_ai_cost or ai_demand == 0
    
    def test_firm_production(self):
        """Test firm produces output given labor inputs."""
        config = SimulationConfig()
        firm = Firm(firm_id=0, config=config)
        
        # Hire some workers
        firm.state.human_workers_employed = 5
        firm.state.ai_workers_employed = 3
        
        output = firm.produce_output()
        
        # Should produce positive output with workers
        assert output > 0
        assert firm.state.output_produced == output
        
        # More workers should produce more output
        firm.state.human_workers_employed = 10
        output_more = firm.produce_output()
        assert output_more > output
    
    def test_firm_profits(self):
        """Test firm profit calculation."""
        config = SimulationConfig()
        firm = Firm(firm_id=0, config=config)
        
        # Setup: hire workers, produce, compute profit
        firm.state.human_workers_employed = 10
        firm.state.ai_workers_employed = 5
        firm.state.posted_wage_human = 0.5
        firm.state.posted_cost_ai = 0.2
        
        output = firm.produce_output()
        
        # With sufficient output and low costs, should be profitable
        profit = firm.compute_profits(output_price=1.0)
        assert profit >= 0, f"Profit should be non-negative, got {profit} with output {output}"
    
    def test_firm_rd_investment(self):
        """Test firm R&D spending reduces AI costs."""
        config = SimulationConfig()
        firm = Firm(firm_id=0, config=config)
        
        # Make profits then spend on R&D
        firm.state.profits = 1000
        firm.state.accumulated_r_and_d = 0
        
        initial_cost = firm.state.posted_cost_ai
        
        firm.make_r_and_d_decision()
        
        # Update posted costs
        firm.post_wages_and_vacancies(1.0)
        
        # With R&D, AI cost should be lower
        assert firm.state.accumulated_r_and_d > 0
        assert firm.state.posted_cost_ai <= initial_cost
    
    def test_firm_exit(self):
        """Test firm exit logic."""
        config = SimulationConfig()
        firm = Firm(firm_id=0, config=config.model_copy())
        
        # Set to exit after 2 loss periods
        firm.config.loss_periods_to_exit = 2
        
        # Should not exit when profitable
        firm.state.profits = 100
        assert not firm.check_exit_condition()
        
        # Trigger first loss - set up high wage costs with low output
        firm.state.human_workers_employed = 5
        firm.state.ai_workers_employed = 0
        firm.state.posted_wage_human = 10.0  # Very high wages
        firm.state.posted_cost_ai = 0.0
        firm.produce_output()  # Will produce some output, but costs >> revenue
        profit1 = firm.compute_profits(output_price=0.1)  # Low output price
        assert profit1 < 0, f"Expected loss, got profit {profit1}"
        assert firm.state.losses_consecutive == 1
        assert not firm.check_exit_condition()
        
        # Trigger second loss with same setup
        profit2 = firm.compute_profits(output_price=0.1)
        assert profit2 < 0
        assert firm.state.losses_consecutive == 2
        assert firm.check_exit_condition()  # Should exit after 2 consecutive losses

    def test_firm_separation(self):
        """Test exogenous worker separation happens in worker.step(), not hire_workers.
        
        Separations are now handled by worker.step() and reconciled in the engine.
        hire_workers() only adds newly matched workers.
        """
        config = SimulationConfig(separation_rate_employed=0.5)  # 50% monthly
        firm = Firm(firm_id=0, config=config)
        
        firm.state.human_workers_employed = 10
        firm.state.ai_workers_employed = 5
        
        np.random.seed(42)
        # hire_workers no longer separates — it only adds new hires
        firm.hire_workers(matched_human=0, matched_ai=0)
        assert firm.state.human_workers_employed == 10  # Unchanged (no separations here)
        assert firm.state.ai_workers_employed == 5
        
        # Verify separation works through worker.step() instead
        worker = Worker(worker_id=99, config=config, skill_level=SkillLevel.LOW)
        worker.state.status = WorkerStatus.EMPLOYED
        worker.state.current_firm = 0
        worker.state.current_wage = 1.0
        
        # With 50% separation rate, running many workers guarantees some separate
        separated = 0
        for _ in range(20):
            w = Worker(worker_id=_, config=config)
            w.state.status = WorkerStatus.EMPLOYED
            w.state.current_firm = 0
            w.state.current_wage = 1.0
            old_status = w.state.status
            w.step(env=None)
            if w.state.status == WorkerStatus.UNEMPLOYED:
                separated += 1
        assert separated > 0  # At least some should separate with 50% rate


class TestWorkerBehavior:
    """Test complete worker agent behavior."""
    
    def test_worker_job_acceptance(self):
        """Test worker accepts job if wage meets reservation."""
        config = SimulationConfig()
        worker = Worker(worker_id=0, config=config)
        
        # Start unemployed
        worker.state.current_wage = 0.5  # From previous employment
        worker.state.status = WorkerStatus.UNEMPLOYED
        
        # Update spell to generate reservation wage
        worker.update_unemployment_spell()
        
        # Accept offer above reservation
        assert worker.receive_job_offer(firm_id=1, wage=worker.state.reservation_wage + 0.1)
        assert worker.state.status == WorkerStatus.EMPLOYED
        assert worker.state.current_firm == 1
    
    def test_worker_job_rejection(self):
        """Test worker rejects job if wage too low."""
        config = SimulationConfig()
        worker = Worker(worker_id=1, config=config)
        
        worker.state.status = WorkerStatus.UNEMPLOYED
        worker.state.current_wage = 0.5
        worker.update_unemployment_spell()
        
        # Reject offer below reservation
        assert not worker.receive_job_offer(firm_id=1, wage=worker.state.reservation_wage - 0.1)
        assert worker.state.status == WorkerStatus.UNEMPLOYED
    
    def test_worker_unemployment_dynamics(self):
        """Test unemployment spell dynamics."""
        config = SimulationConfig()
        worker = Worker(worker_id=2, config=config)
        
        worker.state.status = WorkerStatus.UNEMPLOYED
        worker.state.unemployment_duration = 0
        worker.state.current_wage = 1.0
        initial_savings = worker.state.accumulated_savings
        
        # Update spell
        worker.update_unemployment_spell()
        
        # Duration and savings should increase
        assert worker.state.unemployment_duration == 1
        assert worker.state.accumulated_savings > initial_savings
        
        # Reservation wage should decay with duration
        reservation_t1 = worker.state.reservation_wage
        worker.update_unemployment_spell()
        reservation_t2 = worker.state.reservation_wage
        assert reservation_t2 < reservation_t1  # Decreases with search pressure
    
    def test_worker_entrepreneurship(self):
        """Test worker can start business with sufficient capital."""
        config = SimulationConfig()
        config.min_capital_to_start_firm = 1000
        
        worker = Worker(worker_id=3, config=config)
        worker.state.status = WorkerStatus.UNEMPLOYED
        worker.state.accumulated_savings = 2000  # Above threshold
        
        np.random.seed(42)
        founds = worker.consider_entrepreneurship()
        
        if founds:
            assert worker.state.status == WorkerStatus.ENTREPRENEUR
            assert worker.state.accumulated_savings < 2000  # Capital used
    
    def test_worker_employment_savings(self):
        """Test worker accumulates savings when employed."""
        config = SimulationConfig()
        worker = Worker(worker_id=4, config=config)
        
        worker.state.status = WorkerStatus.EMPLOYED
        worker.state.current_wage = 2.0
        initial_savings = worker.state.accumulated_savings
        
        worker.state.current_firm = 1
        worker.state.unemployment_duration = 0
        
        # Step while employed - should save 10% of wage
        worker.step(env=None)
        
        expected_savings = initial_savings + 2.0 * 0.1
        assert abs(worker.state.accumulated_savings - expected_savings) < 0.01
    
    def test_worker_exogenous_separation(self):
        """Test worker can be separated exogenously."""
        config = SimulationConfig(separation_rate_employed=1.0)  # Always separate
        worker = Worker(worker_id=5, config=config)
        
        worker.state.status = WorkerStatus.EMPLOYED
        worker.state.current_firm = 2
        
        worker.step(env=None)
        
        assert worker.state.status == WorkerStatus.UNEMPLOYED


class TestPhase1Integration:
    """End-to-end tests for Phase 1 components."""
    
    def test_firm_single_period(self):
        """Test single firm execution through one period."""
        config = SimulationConfig()
        firm = Firm(firm_id=0, config=config)
        
        # Mock environment
        class MockEnv:
            market_wage_human = 1.0
            market_ai_cost = 0.5
        
        env = MockEnv()
        
        # Execute period
        firm.step(env)
        
        # Should have history record
        assert len(firm.history) == 1
        assert "output_produced" in firm.history[0]
        assert "profits" in firm.history[0]
    
    def test_worker_multiple_periods(self):
        """Test worker behavior over multiple periods."""
        config = SimulationConfig(separation_rate_employed=0.1)
        worker = Worker(worker_id=0, config=config)
        
        # Start unemployed
        worker.state.status = WorkerStatus.UNEMPLOYED
        
        # Multiple periods of unemployment
        for _ in range(5):
            worker.step(env=None)
        
        # Should accumulate savings from UI
        assert worker.state.accumulated_savings > 0
        assert worker.state.unemployment_duration == 5
