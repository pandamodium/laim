"""Test agent classes."""

import pytest
import numpy as np
from src.config import SimulationConfig
from src.agents import Firm, Worker, SkillLevel, WorkerStatus


class TestFirm:
    """Tests for Firm agent."""
    
    def test_firm_initialization(self):
        """Test firm initialization."""
        config = SimulationConfig()
        firm = Firm(firm_id=0, config=config)
        
        assert firm.agent_id == 0
        assert firm.agent_type == "firm"
        assert firm.state.human_workers_employed == 0
        assert firm.state.capital == 50000.0
    
    def test_firm_state_dict(self):
        """Test firm state export."""
        config = SimulationConfig()
        firm = Firm(firm_id=1, config=config)
        state = firm.get_state()
        
        assert "agent_id" in state
        assert "human_workers_employed" in state
        assert "capital" in state


class TestWorker:
    """Tests for Worker agent."""
    
    def test_worker_initialization(self):
        """Test worker initialization."""
        config = SimulationConfig()
        worker = Worker(worker_id=0, config=config, skill_level=SkillLevel.LOW)
        
        assert worker.agent_id == 0
        assert worker.agent_type == "worker"
        assert worker.state.status == WorkerStatus.UNEMPLOYED
        assert worker.state.skill_level == SkillLevel.LOW
    
    def test_worker_state_dict(self):
        """Test worker state export."""
        config = SimulationConfig()
        worker = Worker(worker_id=1, config=config)
        state = worker.get_state()
        
        assert "agent_id" in state
        assert "status" in state
        assert state["status"] == "unemployed"  # Enum converted to string
