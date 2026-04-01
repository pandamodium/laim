"""
Tests for Phase 7: Visualization & Interactive Dashboards

Tests cover:
- Static plot generation (PlotGenerator)
- Interactive dashboard creation (DashboardBuilder)
- Plot configuration and styling
- Data handling and edge cases
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from src.analytics.plots import PlotGenerator, PlotConfig
from src.analytics.dashboard import DashboardBuilder, DashboardConfig


class TestPlotConfig:
    """Tests for PlotConfig configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PlotConfig()
        assert config.figure_size == (12, 6)
        assert config.dpi == 300
        assert config.style == "darkgrid"
        assert config.format == "png"
    
    def test_custom_config(self):
        """Test custom configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PlotConfig(
                figure_size=(16, 8),
                dpi=150,
                output_dir=Path(tmpdir)
            )
            assert config.figure_size == (16, 8)
            assert config.dpi == 150
            assert config.output_dir == Path(tmpdir)
    
    def test_color_palette_defaults(self):
        """Test color palette initialization."""
        config = PlotConfig()
        assert 'low' in config.palette_skill
        assert 'high' in config.palette_skill
        assert 'aggregate' in config.palette_skill
        assert 'Routine' in config.palette_category
        assert 'Management' in config.palette_category
        assert 'Creative' in config.palette_category
    
    def test_output_directory_creation(self):
        """Test that output directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_plots"
            config = PlotConfig(output_dir=output_dir)
            assert config.output_dir.exists()


class TestPlotGenerator:
    """Tests for PlotGenerator static plots."""
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics DataFrame for testing."""
        periods = np.arange(0, 80)  # 20 years of quarterly data
        return pd.DataFrame({
            'period': periods,
            'unemployment_rate': np.random.uniform(0.03, 0.08, len(periods)),
            'unemployment_rate_low_skill': np.random.uniform(0.05, 0.12, len(periods)),
            'unemployment_rate_high_skill': np.random.uniform(0.02, 0.05, len(periods)),
            'avg_wage_human': 50000 + np.cumsum(np.random.uniform(100, 500, len(periods))),
            'avg_wage_ai': 30000 + np.cumsum(np.random.uniform(50, 200, len(periods))),
            'avg_wage_low_skill': 35000 + np.cumsum(np.random.uniform(50, 200, len(periods))),
            'avg_wage_high_skill': 85000 + np.cumsum(np.random.uniform(200, 500, len(periods))),
            'ai_employment_share': np.linspace(0.1, 0.4, len(periods)),
            'ai_adoption_routine': np.linspace(0.2, 0.6, len(periods)),
            'ai_adoption_management': np.linspace(0.05, 0.15, len(periods)),
            'ai_adoption_creative': np.linspace(0.02, 0.08, len(periods)),
            'total_r_and_d_spending': 1000000 + np.cumsum(np.random.uniform(10000, 50000, len(periods))),
            'r_and_d_spending_routine': 500000 + np.cumsum(np.random.uniform(5000, 20000, len(periods))),
            'r_and_d_spending_management': 300000 + np.cumsum(np.random.uniform(3000, 15000, len(periods))),
            'r_and_d_spending_creative': 200000 + np.cumsum(np.random.uniform(2000, 10000, len(periods))),
            'gini_coefficient': 0.25 + np.linspace(0, 0.1, len(periods)),
            'theil_index': 0.1 + np.linspace(0, 0.05, len(periods)),
            'wage_gap_ratio': 1.5 + np.linspace(0, 0.5, len(periods)),
            'employment_routine': 1000000 - np.linspace(0, 200000, len(periods)),
            'employment_management': 300000 + np.linspace(0, 50000, len(periods)),
            'employment_creative': 200000 + np.linspace(0, 100000, len(periods)),
            'output_per_worker': 100000 + np.cumsum(np.random.uniform(500, 2000, len(periods))),
            'human_avg_productivity': 90000 + np.cumsum(np.random.uniform(500, 1500, len(periods))),
            'ai_avg_productivity': 150000 + np.cumsum(np.random.uniform(1000, 3000, len(periods))),
            'ui_recipients': np.random.uniform(10000, 50000, len(periods)),
            'retraining_active': np.random.uniform(5000, 20000, len(periods)),
            'num_firms': 5000 + np.linspace(0, 500, len(periods)),
            'firm_entry': np.random.uniform(20, 100, len(periods)),
            'firm_exit': np.random.uniform(10, 80, len(periods)),
            'avg_firm_size': 50 + np.linspace(0, 20, len(periods)),
            'herfindahl_index': 0.1 + np.linspace(0, 0.05, len(periods)),
        })
    
    @pytest.fixture
    def plot_generator(self):
        """Create PlotGenerator instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PlotConfig(output_dir=Path(tmpdir))
            yield PlotGenerator(config)
    
    def test_unemployment_timeseries(self, plot_generator, sample_metrics):
        """Test unemployment time series plot."""
        fig, ax = plot_generator.plot_unemployment_timeseries(sample_metrics, save=False)
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_wage_evolution(self, plot_generator, sample_metrics):
        """Test wage evolution plot."""
        fig, ax = plot_generator.plot_wage_evolution(sample_metrics, save=False)
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_ai_adoption(self, plot_generator, sample_metrics):
        """Test AI adoption plot."""
        fig, ax = plot_generator.plot_ai_adoption(sample_metrics, save=False)
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_rd_spending(self, plot_generator, sample_metrics):
        """Test R&D spending plot."""
        fig, ax = plot_generator.plot_rd_spending(sample_metrics, save=False)
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_wage_distribution(self, plot_generator):
        """Test wage distribution plot."""
        wages = np.random.lognormal(10.5, 0.5, 1000)
        fig, axes = plot_generator.plot_wage_distribution(wages, save=False)
        assert fig is not None
        assert len(axes) == 2
        plt.close(fig)
    
    def test_wage_inequality(self, plot_generator, sample_metrics):
        """Test wage inequality plot."""
        fig, ax = plot_generator.plot_wage_inequality(sample_metrics, save=False)
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_wage_gap(self, plot_generator, sample_metrics):
        """Test wage gap plot."""
        fig, ax = plot_generator.plot_wage_gap(sample_metrics, save=False)
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_scenario_comparison(self, plot_generator, sample_metrics):
        """Test scenario comparison plot."""
        scenarios = {
            'Baseline': sample_metrics.copy(),
            'High AI': sample_metrics.copy(),
            'Policy': sample_metrics.copy()
        }
        fig, ax = plot_generator.plot_scenario_comparison(
            scenarios, 'unemployment_rate', 'Unemployment Rate', save=False
        )
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_firm_size_distribution(self, plot_generator):
        """Test firm size distribution plot."""
        firm_sizes = np.random.pareto(1.5, 500) + 1  # Pareto distribution
        fig, axes = plot_generator.plot_firm_size_distribution(firm_sizes, save=False)
        assert fig is not None
        assert len(axes) == 2
        plt.close(fig)
    
    def test_employment_by_category(self, plot_generator, sample_metrics):
        """Test employment by category plot."""
        fig, ax = plot_generator.plot_employment_by_category(sample_metrics, save=False)
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_productivity_growth(self, plot_generator, sample_metrics):
        """Test productivity growth plot."""
        fig, ax = plot_generator.plot_productivity_growth(sample_metrics, save=False)
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_policy_impact(self, plot_generator, sample_metrics):
        """Test policy impact plot."""
        fig, ax = plot_generator.plot_policy_impact(sample_metrics, save=False)
        assert fig is not None
        assert ax is not None
        plt.close(fig)
    
    def test_generate_all_plots(self, plot_generator, sample_metrics):
        """Test generating all available plots."""
        wages = np.random.lognormal(10.5, 0.5, 1000)
        firm_sizes = np.random.pareto(1.5, 500) + 1
        
        plots = plot_generator.generate_all_plots(
            sample_metrics, wages, firm_sizes, verbose=False
        )
        
        assert len(plots) > 0
        assert 'unemployment' in plots
        assert 'wages' in plots
        assert 'ai_adoption' in plots
        
        # Verify files exist
        for name, path in plots.items():
            assert path.exists() or not isinstance(path, Path)


class TestDashboardConfig:
    """Tests for DashboardConfig configuration."""
    
    def test_default_config(self):
        """Test default dashboard configuration."""
        config = DashboardConfig()
        assert config.template == "plotly_white"
        assert config.height == 800
        assert config.color_discrete_map is not None
    
    def test_custom_config(self):
        """Test custom dashboard configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DashboardConfig(
                template="plotly_dark",
                height=600,
                output_dir=Path(tmpdir)
            )
            assert config.template == "plotly_dark"
            assert config.height == 600


class TestDashboardBuilder:
    """Tests for DashboardBuilder interactive dashboards."""
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics DataFrame for testing."""
        periods = np.arange(0, 80)
        return pd.DataFrame({
            'period': periods,
            'unemployment_rate': np.random.uniform(0.03, 0.08, len(periods)),
            'unemployment_rate_low_skill': np.random.uniform(0.05, 0.12, len(periods)),
            'unemployment_rate_high_skill': np.random.uniform(0.02, 0.05, len(periods)),
            'avg_wage_human': 50000 + np.cumsum(np.random.uniform(100, 500, len(periods))),
            'wage_gap_ratio': 1.5 + np.linspace(0, 0.5, len(periods)),
            'ai_employment_share': np.linspace(0.1, 0.4, len(periods)),
            'total_r_and_d_spending': 1000000 + np.cumsum(np.random.uniform(10000, 50000, len(periods))),
            'output_per_worker': 100000 + np.cumsum(np.random.uniform(500, 2000, len(periods))),
            'gini_coefficient': 0.25 + np.linspace(0, 0.1, len(periods)),
            'theil_index': 0.1 + np.linspace(0, 0.05, len(periods)),
            'num_firms': 5000 + np.linspace(0, 500, len(periods)),
            'firm_entry': np.random.uniform(20, 100, len(periods)),
            'firm_exit': np.random.uniform(10, 80, len(periods)),
            'avg_firm_size': 50 + np.linspace(0, 20, len(periods)),
            'herfindahl_index': 0.1 + np.linspace(0, 0.05, len(periods)),
            'ui_recipients': np.random.uniform(10000, 50000, len(periods)),
            'retraining_active': np.random.uniform(5000, 20000, len(periods)),
        })
    
    @pytest.fixture
    def dashboard_builder(self):
        """Create DashboardBuilder instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DashboardConfig(output_dir=Path(tmpdir))
            yield DashboardBuilder(config)
    
    def test_overview_dashboard(self, dashboard_builder, sample_metrics):
        """Test overview dashboard creation."""
        fig = dashboard_builder.create_overview_dashboard(sample_metrics, save=False)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
    
    def test_labor_market_dashboard(self, dashboard_builder, sample_metrics):
        """Test labor market dashboard creation."""
        fig = dashboard_builder.create_labor_market_dashboard(sample_metrics, save=False)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
    
    def test_technology_dashboard(self, dashboard_builder, sample_metrics):
        """Test technology dashboard creation."""
        fig = dashboard_builder.create_technology_dashboard(sample_metrics, save=False)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
    
    def test_firm_dynamics_dashboard(self, dashboard_builder, sample_metrics):
        """Test firm dynamics dashboard creation."""
        fig = dashboard_builder.create_firm_dynamics_dashboard(sample_metrics, save=False)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
    
    def test_inequality_dashboard(self, dashboard_builder, sample_metrics):
        """Test inequality dashboard creation."""
        fig = dashboard_builder.create_inequality_dashboard(sample_metrics, save=False)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
    
    def test_policy_dashboard(self, dashboard_builder, sample_metrics):
        """Test policy dashboard creation."""
        fig = dashboard_builder.create_policy_dashboard(sample_metrics, save=False)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
    
    def test_scenario_comparison_dashboard(self, dashboard_builder, sample_metrics):
        """Test scenario comparison dashboard."""
        scenarios = {
            'Baseline': sample_metrics.copy(),
            'High AI': sample_metrics.copy(),
        }
        fig = dashboard_builder.create_scenario_comparison_dashboard(
            scenarios, 'unemployment_rate', 'Unemployment Rate', save=False
        )
        assert isinstance(fig, go.Figure)
        # Should have traces for both scenarios
        assert len(fig.data) >= 2
    
    def test_model_comparison_dashboard(self, dashboard_builder, sample_metrics):
        """Test model comparison dashboard."""
        baseline = sample_metrics.copy()
        policy = sample_metrics.copy() * 0.95  # Slightly lower values
        policy['period'] = sample_metrics['period']
        
        fig = dashboard_builder.create_model_comparison_dashboard(
            baseline, policy, save=False
        )
        assert isinstance(fig, go.Figure)
    
    def test_generate_all_dashboards(self, dashboard_builder, sample_metrics):
        """Test generating all dashboards."""
        dashboards = dashboard_builder.generate_all_dashboards(
            sample_metrics, verbose=False
        )
        
        assert len(dashboards) > 0
        assert 'overview' in dashboards
        assert 'labor_market' in dashboards
        assert 'technology' in dashboards
    
    def test_generate_all_dashboards_with_scenarios(self, dashboard_builder, sample_metrics):
        """Test generating all dashboards with scenarios."""
        scenarios = {
            'Baseline': sample_metrics.copy(),
            'High AI': sample_metrics.copy(),
        }
        
        dashboards = dashboard_builder.generate_all_dashboards(
            sample_metrics, scenarios, verbose=False
        )
        
        assert len(dashboards) > 0


class TestVisualizationIntegration:
    """Integration tests for visualization system."""
    
    @pytest.fixture
    def sample_metrics(self):
        """Create realistic sample metrics."""
        periods = np.arange(0, 80)
        base_unemployment = 0.05
        base_wage = 50000
        
        unemployment = base_unemployment + 0.02 * np.sin(periods / 10)
        unemployment += np.random.uniform(-0.01, 0.01, len(periods))
        unemployment = np.clip(unemployment, 0.02, 0.10)
        
        wage = base_wage * (1 + 0.02 * np.cumsum(np.ones(len(periods)) * 0.01))
        wage += np.random.uniform(-1000, 1000, len(periods))
        
        return pd.DataFrame({
            'period': periods,
            'unemployment_rate': unemployment,
            'unemployment_rate_low_skill': unemployment + 0.02,
            'unemployment_rate_high_skill': unemployment - 0.01,
            'avg_wage_human': wage,
            'avg_wage_low_skill': wage * 0.7,
            'avg_wage_high_skill': wage * 1.5,
            'ai_employment_share': np.linspace(0.05, 0.35, len(periods)),
            'total_r_and_d_spending': 500000 + np.cumsum(np.random.uniform(5000, 20000, len(periods))),
            'gini_coefficient': 0.2 + np.linspace(0, 0.15, len(periods)),
            'wage_gap_ratio': 1.5 + np.linspace(0, 0.6, len(periods)),
            'output_per_worker': 80000 + np.cumsum(np.random.uniform(200, 800, len(periods))),
        })
    
    def test_plots_and_dashboards_together(self, sample_metrics):
        """Test creating both plots and dashboards from same data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plot_config = PlotConfig(output_dir=Path(tmpdir) / "plots")
            dash_config = DashboardConfig(output_dir=Path(tmpdir) / "dashboards")
            
            plot_gen = PlotGenerator(plot_config)
            dash_gen = DashboardBuilder(dash_config)
            
            # Generate plots
            plots = plot_gen.generate_all_plots(sample_metrics, verbose=False)
            assert len(plots) > 0
            
            # Generate dashboards
            dashboards = dash_gen.generate_all_dashboards(sample_metrics, verbose=False)
            assert len(dashboards) > 0
    
    def test_missing_metrics_handling(self):
        """Test handling of sparse metrics data."""
        # Create minimal metrics
        df = pd.DataFrame({
            'period': np.arange(80),
            'unemployment_rate': np.random.uniform(0.03, 0.08, 80),
            'avg_wage_human': np.random.uniform(40000, 60000, 80),
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PlotConfig(output_dir=Path(tmpdir))
            gen = PlotGenerator(config)
            
            # Should not crash with minimal data
            fig, ax = gen.plot_unemployment_timeseries(df, save=False)
            assert fig is not None
            plt.close(fig)
    
    def test_scenario_comparison_consistency(self, sample_metrics):
        """Test that scenario comparisons are consistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PlotConfig(output_dir=Path(tmpdir))
            gen = PlotGenerator(config)
            
            scenarios = {
                'Baseline': sample_metrics.copy(),
                'Policy': sample_metrics.copy() * 1.05,
            }
            scenarios['Policy']['period'] = sample_metrics['period']
            
            fig, ax = gen.plot_scenario_comparison(
                scenarios, 'unemployment_rate', 'Unemployment', save=False
            )
            
            # Check that both scenarios are plotted
            assert len(ax.lines) >= 2
            plt.close(fig)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
