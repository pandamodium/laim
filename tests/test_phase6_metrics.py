"""
Phase 6 Tests: Comprehensive Metrics & Analytics

Tests for metrics collection, inequality calculations, and analysis.
"""

import pytest
import math
from src.analytics.comprehensive_metrics import (
    MetricsCalculator,
    MetricsTracker,
    PeriodMetrics,
    InequalityAnalyzer,
    LaborMarketAnalyzer,
    TechnologyAnalyzer,
    PolicyAnalyzer,
    ExportManager,
)


class TestMetricsCalculator:
    """Test metrics calculation utilities."""
    
    def test_gini_calculation(self):
        """Gini should measure wage inequality."""
        # Perfect equality
        equal_wages = [10.0, 10.0, 10.0]
        gini_equal = MetricsCalculator.calculate_gini(equal_wages)
        assert gini_equal == pytest.approx(0.0)
        
        # Perfect inequality (one earner, others zero)
        unequal_wages = [0.0, 0.0, 30.0]
        gini_unequal = MetricsCalculator.calculate_gini(unequal_wages)
        assert gini_unequal > 0.5
    
    def test_theil_calculation(self):
        """Theil index should measure wage entropy."""
        equal_wages = [10.0, 10.0, 10.0]
        theil = MetricsCalculator.calculate_theil(equal_wages, 10.0)
        assert theil == pytest.approx(0.0)
        
        unequal_wages = [5.0, 10.0, 20.0]
        mean = 35.0 / 3
        theil_unequal = MetricsCalculator.calculate_theil(unequal_wages, mean)
        assert theil_unequal > 0.0
    
    def test_herfindahl_index(self):
        """Herfindahl should measure concentration."""
        # Equal firm sizes
        equal = MetricsCalculator.calculate_herfindahl([100, 100, 100], 300)
        assert equal == pytest.approx(0.333, abs=0.01)
        
        # Monopoly
        monopoly = MetricsCalculator.calculate_herfindahl([300], 300)
        assert monopoly == pytest.approx(1.0)
    
    def test_wage_gap_ratio(self):
        """Wage gap should measure skill premium."""
        low_skill = [10.0, 10.0]
        high_skill = [15.0, 15.0]
        
        gap = MetricsCalculator.calculate_wage_gap_ratio(low_skill, high_skill)
        assert gap == pytest.approx(1.5)


class TestPeriodMetrics:
    """Test period metrics dataclass."""
    
    def test_metrics_initialization(self):
        """Initialize period metrics."""
        metrics = PeriodMetrics(
            period=1,
            num_employed_human=950,
            num_employed_ai=50,
            num_unemployed=0,
            unemployment_rate=0.0,
            labor_force=1000,
            avg_wage_human=10.0,
            median_wage_human=10.0,
            wage_std_human=1.0,
            min_wage=8.0,
            max_wage=12.0,
            total_output=1000.0,
            output_per_worker=1.0,
            output_per_human_worker=1.05,
            output_per_ai_worker=1.5,
            num_firms=3,
            avg_firm_size=320,
            total_firm_profits=100.0,
            avg_firm_profit=33.3,
            num_firms_positive_profit=3,
            job_vacancies=0,
            job_matches=0,
            job_match_rate=1.0,
            new_firms_entered=0,
            firms_exited=0,
            firm_entry_rate=0.0,
            firm_exit_rate=0.0,
            ai_employment_share=0.05,
            cumulative_ai_adopted=50,
            ai_adoption_rate=0.05,
            total_r_and_d_spending=10.0,
            avg_r_and_d_by_firm=3.33,
            r_and_d_as_share_of_output=0.01,
            gini_coefficient=0.25,
            theil_index=0.1,
            wage_gap_ratio=1.2,
            employment_concentration=0.35
        )
        
        assert metrics.period == 1
        assert metrics.unemployment_rate == 0.0
        assert metrics.ai_employment_share == 0.05
    
    def test_to_dict(self):
        """Metrics should convert to dictionary."""
        metrics = PeriodMetrics(
            period=0,
            num_employed_human=900,
            num_employed_ai=100,
            num_unemployed=0,
            unemployment_rate=0.0,
            labor_force=1000,
            avg_wage_human=10.0,
            median_wage_human=10.0,
            wage_std_human=0.5,
            min_wage=9.0,
            max_wage=11.0,
            total_output=1000.0,
            output_per_worker=1.0,
            output_per_human_worker=1.0,
            output_per_ai_worker=1.5,
            num_firms=3,
            avg_firm_size=333,
            total_firm_profits=150.0,
            avg_firm_profit=50.0,
            num_firms_positive_profit=3,
            job_vacancies=10,
            job_matches=50,
            job_match_rate=0.9,
            new_firms_entered=1,
            firms_exited=0,
            firm_entry_rate=0.33,
            firm_exit_rate=0.0,
            ai_employment_share=0.1,
            cumulative_ai_adopted=100,
            ai_adoption_rate=0.1,
            total_r_and_d_spending=20.0,
            avg_r_and_d_by_firm=6.67,
            r_and_d_as_share_of_output=0.02,
            gini_coefficient=0.3,
            theil_index=0.15,
            wage_gap_ratio=1.3,
            employment_concentration=0.36
        )
        
        d = metrics.to_dict()
        assert d["period"] == 0
        assert d["unemployment_rate"] == 0.0
        assert d["gini_coefficient"] == 0.3


class TestMetricsTracker:
    """Test metrics tracking system."""
    
    def create_sample_metrics(self):
        """Create sample metrics for testing."""
        metrics_list = []
        for period in range(5):
            m = PeriodMetrics(
                period=period,
                num_employed_human=950 - period * 10,
                num_employed_ai=50 + period * 10,
                num_unemployed=0,
                unemployment_rate=0.0,
                labor_force=1000,
                avg_wage_human=10.0 - period * 0.1,
                median_wage_human=10.0 - period * 0.1,
                wage_std_human=1.0,
                min_wage=8.0,
                max_wage=12.0,
                total_output=1000.0 + period * 10,
                output_per_worker=1.0 + period * 0.01,
                output_per_human_worker=1.0 + period * 0.01,
                output_per_ai_worker=1.5,
                num_firms=3,
                avg_firm_size=320,
                total_firm_profits=100.0 + period * 10,
                avg_firm_profit=33.3,
                num_firms_positive_profit=3,
                job_vacancies=0,
                job_matches=50,
                job_match_rate=1.0,
                new_firms_entered=0,
                firms_exited=0,
                firm_entry_rate=0.0,
                firm_exit_rate=0.0,
                ai_employment_share=0.05 + period * 0.01,
                cumulative_ai_adopted=50 + period * 10,
                ai_adoption_rate=0.05,
                total_r_and_d_spending=10.0,
                avg_r_and_d_by_firm=3.33,
                r_and_d_as_share_of_output=0.01,
                gini_coefficient=0.25 + period * 0.01,
                theil_index=0.1 + period * 0.01,
                wage_gap_ratio=1.2 + period * 0.05,
                employment_concentration=0.35
            )
            metrics_list.append(m)
        return metrics_list
    
    def test_tracker_initialization(self):
        """Tracker should initialize empty."""
        tracker = MetricsTracker()
        assert len(tracker.period_metrics) == 0
    
    def test_add_metrics(self):
        """Tracker should add metrics."""
        tracker = MetricsTracker()
        metrics = self.create_sample_metrics()
        
        for m in metrics:
            tracker.add_period_metrics(m)
        
        assert len(tracker.period_metrics) == 5
        assert tracker.current_period == metrics[-1]
    
    def test_get_period(self):
        """Tracker should retrieve metrics by period."""
        tracker = MetricsTracker()
        metrics = self.create_sample_metrics()
        
        for m in metrics:
            tracker.add_period_metrics(m)
        
        retrieved = tracker.get_period(2)
        assert retrieved is not None
        assert retrieved.period == 2
        assert retrieved.ai_employment_share == pytest.approx(0.07)
    
    def test_metric_series(self):
        """Tracker should return time series."""
        tracker = MetricsTracker()
        metrics = self.create_sample_metrics()
        
        for m in metrics:
            tracker.add_period_metrics(m)
        
        series = tracker.get_metric_series("ai_employment_share")
        assert len(series) == 5
        assert series[0] == (0, 0.05)
        assert series[-1] == (4, 0.09)
    
    def test_average_calculation(self):
        """Tracker should calculate metric averages."""
        tracker = MetricsTracker()
        metrics = self.create_sample_metrics()
        
        for m in metrics:
            tracker.add_period_metrics(m)
        
        avg_ai_share = tracker.calculate_average("ai_employment_share")
        expected = (0.05 + 0.06 + 0.07 + 0.08 + 0.09) / 5
        assert avg_ai_share == pytest.approx(expected)
    
    def test_trend_calculation(self):
        """Tracker should calculate metric trends."""
        tracker = MetricsTracker()
        metrics = self.create_sample_metrics()
        
        for m in metrics:
            tracker.add_period_metrics(m)
        
        # AI adoption rising linearly
        trend = tracker.calculate_trend("ai_employment_share")
        assert trend > 0  # Positive trend


class TestInequalityAnalyzer:
    """Test inequality analysis."""
    
    def test_inequality_evolution(self):
        """Analyzer should track inequality evolution."""
        tracker = MetricsTracker()
        metrics_list = []
        
        for period in range(3):
            m = PeriodMetrics(
                period=period,
                num_employed_human=1000,
                num_employed_ai=0,
                num_unemployed=0,
                unemployment_rate=0.0,
                labor_force=1000,
                avg_wage_human=10.0,
                median_wage_human=10.0,
                wage_std_human=1.0,
                min_wage=9.0,
                max_wage=11.0,
                total_output=1000.0,
                output_per_worker=1.0,
                output_per_human_worker=1.0,
                output_per_ai_worker=0.0,
                num_firms=1,
                avg_firm_size=1000,
                total_firm_profits=100.0,
                avg_firm_profit=100.0,
                num_firms_positive_profit=1,
                job_vacancies=0,
                job_matches=0,
                job_match_rate=0.0,
                new_firms_entered=0,
                firms_exited=0,
                firm_entry_rate=0.0,
                firm_exit_rate=0.0,
                ai_employment_share=0.0,
                cumulative_ai_adopted=0,
                ai_adoption_rate=0.0,
                total_r_and_d_spending=0.0,
                avg_r_and_d_by_firm=0.0,
                r_and_d_as_share_of_output=0.0,
                gini_coefficient=0.2 + period * 0.05,
                theil_index=0.1 + period * 0.02,
                wage_gap_ratio=1.1 + period * 0.1,
                employment_concentration=1.0
            )
            tracker.add_period_metrics(m)
        
        analyzer = InequalityAnalyzer(tracker)
        evolution = analyzer.get_inequality_evolution()
        
        assert "gini" in evolution
        assert "theil" in evolution
        assert "wage_gap" in evolution
        assert len(evolution["gini"]) == 3


class TestTechnologyAnalyzer:
    """Test technology analyzer."""
    
    def test_adoption_path(self):
        """Analyzer should track adoption path."""
        tracker = MetricsTracker()
        
        for period in range(5):
            m = PeriodMetrics(
                period=period,
                num_employed_human=1000 - period * 50,
                num_employed_ai=period * 50,
                num_unemployed=0,
                unemployment_rate=0.0,
                labor_force=1000,
                avg_wage_human=10.0,
                median_wage_human=10.0,
                wage_std_human=1.0,
                min_wage=9.0,
                max_wage=11.0,
                total_output=1000.0 + period * 50,
                output_per_worker=1.0 + period * 0.01,
                output_per_human_worker=1.0,
                output_per_ai_worker=1.5,
                num_firms=3,
                avg_firm_size=333,
                total_firm_profits=100.0,
                avg_firm_profit=33.3,
                num_firms_positive_profit=3,
                job_vacancies=0,
                job_matches=0,
                job_match_rate=0.0,
                new_firms_entered=0,
                firms_exited=0,
                firm_entry_rate=0.0,
                firm_exit_rate=0.0,
                ai_employment_share=period * 0.05,
                cumulative_ai_adopted=period * 50,
                ai_adoption_rate=0.05,
                total_r_and_d_spending=10.0 * (period + 1),
                avg_r_and_d_by_firm=3.33,
                r_and_d_as_share_of_output=0.01,
                gini_coefficient=0.25,
                theil_index=0.1,
                wage_gap_ratio=1.2,
                employment_concentration=0.35
            )
            tracker.add_period_metrics(m)
        
        analyzer = TechnologyAnalyzer(tracker)
        path = analyzer.get_adoption_path()
        
        assert len(path) == 5
        assert path[0][1] == 0.0
        assert path[-1][1] == 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
