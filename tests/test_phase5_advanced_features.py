"""
Phase 5 Tests: Advanced Economics Features

Tests for policy interventions, skill-based technical change, and AI cost dynamics.
"""

import pytest
from src.config.parameters import SimulationConfig, create_custom_config
from src.policy.interventions import (
    UIBenefitTracker,
    RetrainingProgramTracker,
    WageSubsidyTracker,
    TaxCreditTracker,
    PolicyModule,
)
from src.market.skill_dynamics import (
    SkillLevel,
    JobCategory,
    SkillHeterogeneoitModel,
    JobCategoryMarket,
    WagePolarizationModel,
)
from src.market.ai_cost_dynamics import (
    AICostTracker,
    AIProductivityBoost,
    MarketAIDynamics,
    CostCurveAnalyzer,
)


# ========== Policy Intervention Tests ==========

class TestUnemploymentInsurance:
    """Test UI benefit tracking and management."""
    
    def test_ui_benefit_creation(self):
        """UI benefit should be created and active."""
        tracker = UIBenefitTracker()
        benefit = tracker.create_benefit(
            worker_id=1,
            start_period=0,
            duration=26,
            amount=1000.0
        )
        
        assert benefit.worker_id == 1
        assert benefit.is_active()
        assert tracker.get_benefit_amount(1) == 1000.0
    
    def test_ui_benefit_duration(self):
        """UI benefits should expire after duration periods."""
        tracker = UIBenefitTracker()
        tracker.create_benefit(
            worker_id=1,
            start_period=0,
            duration=2,
            amount=500.0
        )
        
        # Should be active
        assert tracker.get_benefit_amount(1) == 500.0
        
        # After 2 periods, should expire
        for _ in range(2):
            tracker.apply_period()
        
        assert tracker.get_benefit_amount(1) is None
    
    def test_ui_statistics(self):
        """UI tracker should report accurate statistics."""
        tracker = UIBenefitTracker()
        tracker.create_benefit(1, 0, 26, 600.0)
        tracker.create_benefit(2, 0, 26, 400.0)
        
        stats = tracker.get_statistics()
        assert stats["active_recipients"] == 2
        assert stats["total_spent"] == 0.0  # Not yet recorded


class TestRetrainingPrograms:
    """Test retraining program mechanics."""
    
    def test_program_enrollment(self):
        """Worker should enroll in retraining."""
        tracker = RetrainingProgramTracker()
        program = tracker.enroll_worker(
            worker_id=1,
            start_period=0,
            duration=8,
            cost=5000.0,
            success_rate=0.7,
            boost=0.15
        )
        
        assert program.worker_id == 1
        assert program.status == "in_progress"
        assert tracker.total_cost == 5000.0
    
    def test_program_completion(self):
        """Program should complete after duration."""
        tracker = RetrainingProgramTracker()
        tracker.enroll_worker(1, 0, 3, 5000.0, 0.7, 0.15)
        
        # Apply 3 periods
        for _ in range(3):
            tracker.apply_period()
        
        program = tracker.completed_programs[1]
        assert program.status == "completed"
    
    def test_program_success_rate(self):
        """Tracker should count graduates."""
        tracker = RetrainingProgramTracker()
        tracker.enroll_worker(1, 0, 1, 5000.0, 0.7, 0.15)
        tracker.apply_period()
        
        tracker.graduate_worker(1, success=True)
        stats = tracker.get_statistics()
        
        assert stats["total_graduates"] == 1
        assert stats["success_rate"] == 1.0  # 100% (only 1 completed)
    
    def test_productivity_boost_after_graduation(self):
        """Graduated workers should receive productivity boost."""
        tracker = RetrainingProgramTracker()
        tracker.enroll_worker(1, 0, 1, 5000.0, 0.7, 0.25)
        tracker.apply_period()
        tracker.graduate_worker(1, success=True)
        
        boost = tracker.get_program_boost(1)
        assert boost == 0.25


class TestTaxCredits:
    """Test tax credit system."""
    
    def test_r_and_d_tax_credit(self):
        """R&D spending should qualify for tax credit."""
        tracker = TaxCreditTracker(r_and_d_enabled=True, r_and_d_rate=0.25)
        
        credit = tracker.calculate_r_and_d_credit(1000.0)
        assert credit == 250.0  # 25% of 1000
    
    def test_hiring_tax_credit(self):
        """New hires should generate tax credit."""
        tracker = TaxCreditTracker(hiring_enabled=True, hiring_amount=2000.0)
        
        credit = tracker.calculate_hiring_credit(5)
        assert credit == 10000.0  # 5 × 2000
    
    def test_tax_credit_application(self):
        """Tax credits should be applied and retrieved."""
        tracker = TaxCreditTracker(
            r_and_d_enabled=True,
            r_and_d_rate=0.2,
            hiring_enabled=True,
            hiring_amount=1500.0
        )
        
        tracker.apply_credits_to_firm(1, r_and_d_spending=10000.0, net_hires=3)
        r_and_d, hiring = tracker.get_credits(1)
        
        assert r_and_d == 2000.0  # 20% of 10000
        assert hiring == 4500.0   # 3 × 1500


class TestPolicyModule:
    """Test integrated policy module."""
    
    def test_policy_module_initialization(self):
        """Policy module should initialize all systems."""
        config = create_custom_config(
            wage_subsidy_enabled=True,
            r_and_d_tax_credit_enabled=True
        )
        policy = PolicyModule(config)
        
        assert policy.ui_tracker is not None
        assert policy.retraining_tracker is not None
        assert policy.subsidy_tracker.enabled
        assert policy.tax_credit_tracker.r_and_d_enabled
    
    def test_policy_period_application(self):
        """Policy module should apply all updates each period."""
        config = create_custom_config()
        policy = PolicyModule(config)
        
        policy.ui_tracker.create_benefit(1, 0, 2, 500.0)
        policy.apply_period()
        
        # After one period, should still be active
        assert policy.ui_tracker.get_benefit_amount(1) is not None


# ========== Skill-Based Technical Change Tests ==========

class TestSkillHeterogeneity:
    """Test skill heterogeneity model."""
    
    def test_skill_assignment(self):
        """Workers should be assigned skill levels."""
        config = create_custom_config(
            use_skill_heterogeneity=True,
            skill_distribution_low_share=0.5
        )
        model = SkillHeterogeneoitModel(config)
        
        # Draws < 0.5 should be low-skill
        skill = model.assign_skill_level(0.3)
        assert skill == SkillLevel.LOW
        
        # Draws >= 0.5 should be high-skill
        skill = model.assign_skill_level(0.7)
        assert skill == SkillLevel.HIGH
    
    def test_skill_job_matching(self):
        """Skill-job matching should reflect quality."""
        config = create_custom_config(use_skill_heterogeneity=True)
        model = SkillHeterogeneoitModel(config)
        
        # High-skill always matches
        assert model.is_skill_match(SkillLevel.HIGH, JobCategory.ROUTINE)
        assert model.is_skill_match(SkillLevel.HIGH, JobCategory.CREATIVE)
        
        # Low-skill matches routine best
        assert model.is_skill_match(SkillLevel.LOW, JobCategory.ROUTINE)
        assert not model.is_skill_match(SkillLevel.LOW, JobCategory.CREATIVE)
    
    def test_skill_match_bonus(self):
        """Match bonuses should reflect productivity."""
        config = create_custom_config(use_skill_heterogeneity=True)
        model = SkillHeterogeneoitModel(config)
        
        # Low-skill in routine: bonus
        bonus = model.get_match_bonus(SkillLevel.LOW, JobCategory.ROUTINE)
        assert bonus > 1.0
        
        # High-skill in creative: bonus
        bonus = model.get_match_bonus(SkillLevel.HIGH, JobCategory.CREATIVE)
        assert bonus > 1.0
        
        # Mismatches should have penalties
        bonus = model.get_match_bonus(SkillLevel.LOW, JobCategory.CREATIVE)
        assert bonus < 1.0
    
    def test_wage_gap_calculation(self):
        """Wage gap should reflect skill premium."""
        config = create_custom_config(use_skill_heterogeneity=True)
        model = SkillHeterogeneoitModel(config)
        
        model.update_wage_by_skill(10.0, 12.0)
        gap = model.get_wage_gap_ratio()
        assert gap == pytest.approx(1.2)


class TestJobCategoryMarket:
    """Test job category market."""
    
    def test_job_category_profiles(self):
        """Job categories should have defined profiles."""
        config = create_custom_config(use_job_categories=True)
        market = JobCategoryMarket(config)
        
        assert JobCategory.ROUTINE in market.categories
        assert JobCategory.MANAGEMENT in market.categories
        assert JobCategory.CREATIVE in market.categories
    
    def test_ai_adoption_by_category(self):
        """AI adoption should differ by category."""
        config = create_custom_config(use_job_categories=True)
        market = JobCategoryMarket(config)
        
        market.update_ai_adoption(JobCategory.ROUTINE, 0.1)
        market.update_ai_adoption(JobCategory.CREATIVE, 0.02)
        
        adoption = market.get_ai_adoption_per_category()
        assert adoption[JobCategory.ROUTINE] == 0.1
        assert adoption[JobCategory.CREATIVE] == 0.02
    
    def test_ai_cost_by_category(self):
        """AI cost should reflect productivity."""
        config = create_custom_config(
            use_job_categories=True,
            ai_wage_ratio=0.5
        )
        market = JobCategoryMarket(config)
        
        # Routine has high AI productivity, so low effective cost
        routine_cost = market.get_ai_cost_in_category(JobCategory.ROUTINE, 0.5)
        assert routine_cost < 0.5
        
        # Creative has low AI productivity, so high effective cost
        creative_cost = market.get_ai_cost_in_category(JobCategory.CREATIVE, 0.5)
        assert creative_cost > 0.5
    
    def test_displacement_calculation(self):
        """Displacement should scale with adoption."""
        config = create_custom_config(use_job_categories=True)
        market = JobCategoryMarket(config)
        
        market.update_ai_adoption(JobCategory.ROUTINE, 0.2)
        
        # With 20% adoption and 100 workers, should displace 20
        displacement = market.calculate_displacement(JobCategory.ROUTINE, 100)
        assert displacement == 20


class TestWagePolarization:
    """Test wage polarization dynamics."""
    
    def test_polarization_index(self):
        """Polarization index should reflect wage gap."""
        config = create_custom_config(use_skill_heterogeneity=True)
        skill_model = SkillHeterogeneoitModel(config)
        job_market = JobCategoryMarket(config)
        polarization = WagePolarizationModel(config, skill_model, job_market)
        
        skill_model.update_wage_by_skill(10.0, 15.0)
        index = polarization.get_polarization_index()
        assert index == pytest.approx(1.5)
    
    def test_wage_adjustment_for_routine_jobs(self):
        """Routine jobs should face wage pressure from AI."""
        config = create_custom_config(use_job_categories=True)
        skill_model = SkillHeterogeneoitModel(config)
        job_market = JobCategoryMarket(config)
        polarization = WagePolarizationModel(config, skill_model, job_market)
        
        # High AI adoption and employment should compress routine wages
        adjusted_wage = polarization.calculate_wage_adjustment_for_category(
            JobCategory.ROUTINE,
            current_wage=10.0,
            ai_adoption_rate=0.3,
            unemployment_rate=0.05
        )
        
        assert adjusted_wage < 10.0  # Wages should fall


# ========== AI Cost Dynamics Tests ==========

class TestAICostCurve:
    """Test AI cost curve learning."""
    
    def test_ai_cost_reduction_with_adoption(self):
        """AI costs should decrease with cumulative adoption."""
        tracker = AICostTracker(
            base_ai_cost=0.5,
            learning_parameter=0.3
        )
        
        # Initial cost
        initial = tracker.get_cost()
        assert initial == pytest.approx(0.5)
        
        # After adopting 1000 units
        tracker.apply_period(ai_hired_this_period=1000, r_and_d_spending=0)
        cost_after_adoption = tracker.get_cost()
        
        assert cost_after_adoption < initial
    
    def test_r_and_d_cost_reduction(self):
        """R&D spending should reduce AI costs."""
        tracker = AICostTracker(
            base_ai_cost=0.5,
            learning_parameter=0.0,  # No learning curve
            r_and_d_cost_reduction_rate=0.002
        )
        
        initial = tracker.get_cost()
        
        # $1M of R&D with rate 0.002 should reduce cost by 0.002
        tracker.apply_period(ai_hired_this_period=0, r_and_d_spending=1_000_000)
        cost_after_rd = tracker.get_cost()
        
        reduction = initial - cost_after_rd
        assert reduction == pytest.approx(0.002, abs=0.0001)
    
    def test_cost_statistics(self):
        """Cost tracker should report accurate statistics."""
        tracker = AICostTracker(base_ai_cost=1.0, learning_parameter=0.3)
        tracker.apply_period(500, 5000)
        
        stats = tracker.get_statistics()
        assert stats["base_ai_cost"] == 1.0
        assert stats["current_ai_cost"] < 1.0
        assert stats["cumulative_ai_adopted"] == 500


class TestAIProductivityBoost:
    """Test AI productivity improvements."""
    
    def test_base_productivity(self):
        """AI should have base productivity."""
        boost = AIProductivityBoost(base_productivity=1.5, learning_rate=0.05)
        assert boost.get_productivity_multiplier() == 1.5
    
    def test_learning_from_deployment(self):
        """Productivity should improve with deployment."""
        boost = AIProductivityBoost(base_productivity=1.5, learning_rate=0.05)
        boost.apply_period(ai_employed_this_period=1000, r_and_d_productivity_boost=0)
        
        new_productivity = boost.get_productivity_multiplier()
        assert new_productivity > 1.5
    
    def test_r_and_d_productivity_boost(self):
        """R&D should boost productivity."""
        boost = AIProductivityBoost(base_productivity=1.5)
        boost.apply_period(ai_employed_this_period=0, r_and_d_productivity_boost=0.3)
        
        assert boost.get_productivity_multiplier() == pytest.approx(1.8)


class TestMarketAIDynamics:
    """Test market-level AI dynamics."""
    
    def test_dynamics_initialization(self):
        """Market dynamics should initialize correctly."""
        config = create_custom_config(ai_cost_curve_learning_enabled=True)
        dynamics = MarketAIDynamics(config)
        
        assert dynamics.enabled
        assert dynamics.cost_tracker is not None
        assert dynamics.productivity_tracker is not None
    
    def test_period_application(self):
        """Market dynamics should update each period."""
        config = create_custom_config(ai_cost_curve_learning_enabled=True)
        dynamics = MarketAIDynamics(config)
        
        initial_cost = dynamics.get_ai_cost_for_firm(1)
        initial_productivity = dynamics.get_ai_productivity_for_firm(1)
        
        # Apply period with adoption
        dynamics.apply_period(total_ai_hired=500, total_r_and_d_spending=50000)
        
        final_cost = dynamics.get_ai_cost_for_firm(1)
        final_productivity = dynamics.get_ai_productivity_for_firm(1)
        
        assert final_cost < initial_cost  # Cost should fall
        assert final_productivity > initial_productivity  # Productivity should rise
    
    def test_spillover_effect(self):
        """All firms should benefit from market-level cost reductions."""
        config = create_custom_config(ai_cost_curve_learning_enabled=True)
        dynamics = MarketAIDynamics(config)
        
        dynamics.apply_period(total_ai_hired=1000, total_r_and_d_spending=100000)
        
        # All firms should see same cost
        cost1 = dynamics.get_ai_cost_for_firm(1)
        cost2 = dynamics.get_ai_cost_for_firm(2)
        
        assert cost1 == cost2


class TestCostCurveAnalyzer:
    """Test cost curve analysis utilities."""
    
    def test_elasticity_calculation(self):
        """Elasticity should be constant for exponential form."""
        elasticity = CostCurveAnalyzer.cost_elasticity_to_adoption(
            base_cost=1.0,
            cumulative_adoption=100,
            learning_param=0.3
        )
        
        assert elasticity == pytest.approx(-0.3)
    
    def test_cost_breakeven_analysis(self):
        """Breakeven analysis should identify when AI becomes cheaper."""
        breakeven = CostCurveAnalyzer.cost_breakeven_analysis(
            human_wage=10.0,
            ai_cost=5.0,
            ai_productivity=2.0
        )
        
        assert breakeven["cost_advantage_for_ai"]
        assert breakeven["ai_cost_advantage_pct"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
