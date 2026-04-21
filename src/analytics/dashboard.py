"""
Phase 7: Interactive dashboard for exploring simulation results.

This module provides interactive Plotly-based dashboards for exploring
simulation outputs across multiple dimensions (labor market, technology,
firm dynamics, policy, and scenarios).

Classes:
    DashboardBuilder: Main class for creating interactive dashboards
    DashboardConfig: Configuration for dashboard appearance and behavior
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DashboardConfig:
    """Configuration for interactive dashboards."""
    
    # Theme and colors
    template: str = "plotly_white"
    color_discrete_map: Dict[str, str] = None
    height: int = 800
    
    # Output
    output_dir: Path = None
    
    def __post_init__(self):
        """Set defaults for color mapping."""
        if self.color_discrete_map is None:
            self.color_discrete_map = {
                'unemployment': '#e74c3c',
                'wage': '#3498db',
                'ai_adoption': '#9b59b6',
                'r_and_d': '#e67e22',
                'gini': '#e74c3c',
                'output': '#27ae60',
            }
        
        if self.output_dir is None:
            self.output_dir = Path('outputs/dashboards')
        self.output_dir.mkdir(parents=True, exist_ok=True)


class DashboardBuilder:
    """Build interactive Plotly dashboards from simulation metrics."""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        """
        Initialize the dashboard builder.
        
        Args:
            config: DashboardConfig instance. If None, uses defaults.
        """
        self.config = config or DashboardConfig()
    
    def create_overview_dashboard(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'overview_dashboard.html'
    ) -> go.Figure:
        """
        Create overview dashboard with key macro metrics.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            save: Whether to save the dashboard
            filename: Output filename
            
        Returns:
            Plotly Figure object
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Unemployment Rate',
                'Average Wage',
                'AI Employment Share',
                'R&D Spending'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'scatter'}],
                [{'type': 'scatter'}, {'type': 'scatter'}]
            ]
        )
        
        # Unemployment rate
        if 'unemployment_rate' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['unemployment_rate'],
                    mode='lines+markers',
                    name='Unemployment',
                    line=dict(color='#e74c3c', width=2),
                    marker=dict(size=6)
                ),
                row=1, col=1
            )
        
        # Average wage
        if 'avg_wage_human' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['avg_wage_human'],
                    mode='lines+markers',
                    name='Avg Wage',
                    line=dict(color='#3498db', width=2),
                    marker=dict(size=6)
                ),
                row=1, col=2
            )
        
        # AI employment share
        if 'ai_employment_share' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['ai_employment_share'],
                    mode='lines+markers',
                    name='AI Share',
                    line=dict(color='#9b59b6', width=2),
                    marker=dict(size=6)
                ),
                row=2, col=1
            )
        
        # R&D spending
        if 'total_r_and_d_spending' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['total_r_and_d_spending'],
                    mode='lines+markers',
                    name='R&D Spending',
                    line=dict(color='#e67e22', width=2),
                    marker=dict(size=6)
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title_text="Simulation Overview Dashboard",
            showlegend=False,
            height=self.config.height,
            template=self.config.template,
            hovermode='x unified'
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Period (Quarters)", row=2, col=1)
        fig.update_xaxes(title_text="Period (Quarters)", row=2, col=2)
        fig.update_yaxes(title_text="Rate", row=1, col=1)
        fig.update_yaxes(title_text="Wage ($)", row=1, col=2)
        fig.update_yaxes(title_text="Share", row=2, col=1)
        fig.update_yaxes(title_text="Spending ($)", row=2, col=2)
        
        if save:
            self._save_dashboard(fig, filename)
        
        return fig
    
    def create_labor_market_dashboard(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'labor_market_dashboard.html'
    ) -> go.Figure:
        """
        Create interactive labor market dashboard.
        
        Features: Unemployment, wages, skill-level metrics, distributions.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            save: Whether to save the dashboard
            filename: Output filename
            
        Returns:
            Plotly Figure object
        """
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Unemployment rate (left axis)
        if 'unemployment_rate' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['unemployment_rate'],
                    mode='lines+markers',
                    name='Overall Unemployment',
                    line=dict(color='#e74c3c', width=2.5),
                    marker=dict(size=6)
                ),
                secondary_y=False
            )
        
        # Skill-level unemployment if available
        if 'unemployment_rate_low_skill' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['unemployment_rate_low_skill'],
                    mode='lines',
                    name='Low-Skill Unemployment',
                    line=dict(color='#e74c3c', width=1.5, dash='dash'),
                ),
                secondary_y=False
            )
        
        if 'unemployment_rate_high_skill' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['unemployment_rate_high_skill'],
                    mode='lines',
                    name='High-Skill Unemployment',
                    line=dict(color='#27ae60', width=1.5, dash='dash'),
                ),
                secondary_y=False
            )
        
        # Wage gap on right axis
        if 'wage_gap_ratio' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['wage_gap_ratio'],
                    mode='lines+markers',
                    name='Wage Gap (H/L)',
                    line=dict(color='#3498db', width=2.5),
                    marker=dict(size=6, symbol='diamond')
                ),
                secondary_y=True
            )
        
        # Update layout
        fig.update_layout(
            title_text="Labor Market Dashboard",
            hovermode='x unified',
            height=self.config.height,
            template=self.config.template,
            legend=dict(x=0, y=1, bgcolor='rgba(255, 255, 255, 0.8)')
        )
        
        fig.update_xaxes(title_text="Period (Quarters)")
        fig.update_yaxes(title_text="Unemployment Rate (%)", secondary_y=False)
        fig.update_yaxes(title_text="Wage Gap Ratio", secondary_y=True)
        
        if save:
            self._save_dashboard(fig, filename)
        
        return fig
    
    def create_technology_dashboard(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'technology_dashboard.html'
    ) -> go.Figure:
        """
        Create interactive technology and R&D dashboard.
        
        Features: AI adoption, R&D spending, productivity.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            save: Whether to save the dashboard
            filename: Output filename
            
        Returns:
            Plotly Figure object
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'AI Employment Share',
                'R&D Spending',
                'Productivity Growth',
                'AI Cost Index'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'scatter'}],
                [{'type': 'scatter'}, {'type': 'scatter'}]
            ]
        )
        
        # AI employment share
        if 'ai_employment_share' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['ai_employment_share'],
                    mode='lines+markers',
                    name='AI Share',
                    line=dict(color='#9b59b6', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(155, 89, 182, 0.2)'
                ),
                row=1, col=1
            )
        
        # R&D spending
        if 'total_r_and_d_spending' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['total_r_and_d_spending'],
                    mode='lines+markers',
                    name='R&D Spending',
                    line=dict(color='#e67e22', width=2)
                ),
                row=1, col=2
            )
        
        # Productivity
        if 'output_per_worker' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['output_per_worker'],
                    mode='lines+markers',
                    name='Productivity',
                    line=dict(color='#27ae60', width=2)
                ),
                row=2, col=1
            )
        
        # AI cost index if available
        if 'ai_cost_index' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['ai_cost_index'],
                    mode='lines+markers',
                    name='AI Cost',
                    line=dict(color='#e74c3c', width=2)
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title_text="Technology & R&D Dashboard",
            showlegend=False,
            height=self.config.height,
            template=self.config.template,
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Period", row=2, col=1)
        fig.update_xaxes(title_text="Period", row=2, col=2)
        
        if save:
            self._save_dashboard(fig, filename)
        
        return fig
    
    def create_firm_dynamics_dashboard(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'firm_dynamics_dashboard.html'
    ) -> go.Figure:
        """
        Create interactive firm dynamics dashboard.
        
        Features: Entry/exit, firm size distribution, profitability, concentration.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            save: Whether to save the dashboard
            filename: Output filename
            
        Returns:
            Plotly Figure object
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Number of Firms',
                'Entry/Exit Flows',
                'Market Concentration',
                'Average Firm Size'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'bar'}],
                [{'type': 'scatter'}, {'type': 'scatter'}]
            ]
        )
        
        # Number of firms
        if 'num_firms' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['num_firms'],
                    mode='lines+markers',
                    name='Num Firms',
                    line=dict(color='#3498db', width=2),
                    fill='tozeroy'
                ),
                row=1, col=1
            )
        
        # Entry/exit
        entry_col = next((c for c in ['firm_entry', 'new_firms_entered'] if c in metrics_df.columns), None)
        exit_col = next((c for c in ['firm_exit', 'firms_exited'] if c in metrics_df.columns), None)
        if entry_col and exit_col:
            fig.add_trace(
                go.Bar(
                    x=metrics_df['period'],
                    y=metrics_df[entry_col],
                    name='Entry',
                    marker=dict(color='#27ae60'),
                    opacity=0.7
                ),
                row=1, col=2
            )
            fig.add_trace(
                go.Bar(
                    x=metrics_df['period'],
                    y=metrics_df[exit_col],
                    name='Exit',
                    marker=dict(color='#e74c3c'),
                    opacity=0.7
                ),
                row=1, col=2
            )
        
        # Market concentration (Herfindahl if available)
        if 'herfindahl_index' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['herfindahl_index'],
                    mode='lines+markers',
                    name='HHI',
                    line=dict(color='#f39c12', width=2)
                ),
                row=2, col=1
            )
        
        # Average firm size
        if 'avg_firm_size' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['avg_firm_size'],
                    mode='lines+markers',
                    name='Avg Size',
                    line=dict(color='#9b59b6', width=2)
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title_text="Firm Dynamics Dashboard",
            showlegend=True,
            height=self.config.height + 100,
            template=self.config.template,
            hovermode='x unified'
        )
        
        if save:
            self._save_dashboard(fig, filename)
        
        return fig
    
    def create_inequality_dashboard(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'inequality_dashboard.html'
    ) -> go.Figure:
        """
        Create interactive inequality and distribution dashboard.
        
        Features: Gini, Theil, wage gap, skill differentials.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            save: Whether to save the dashboard
            filename: Output filename
            
        Returns:
            Plotly Figure object
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Gini coefficient
        if 'gini_coefficient' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['gini_coefficient'],
                    mode='lines+markers',
                    name='Gini',
                    line=dict(color='#e74c3c', width=2.5),
                    marker=dict(size=6)
                ),
                secondary_y=False
            )
        
        # Theil index
        if 'theil_index' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['theil_index'],
                    mode='lines+markers',
                    name='Theil',
                    line=dict(color='#3498db', width=2.5),
                    marker=dict(size=6, symbol='diamond')
                ),
                secondary_y=True
            )
        
        # Wage gap
        if 'wage_gap_ratio' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['wage_gap_ratio'],
                    mode='lines',
                    name='Wage Gap',
                    line=dict(color='#f39c12', width=2, dash='dash'),
                ),
                secondary_y=False
            )
        
        fig.update_layout(
            title_text="Inequality & Distribution Dashboard",
            hovermode='x unified',
            height=self.config.height,
            template=self.config.template,
            legend=dict(x=0, y=1, bgcolor='rgba(255, 255, 255, 0.8)')
        )
        
        fig.update_xaxes(title_text="Period (Quarters)")
        fig.update_yaxes(title_text="Gini / Wage Gap", secondary_y=False)
        fig.update_yaxes(title_text="Theil Index", secondary_y=True)
        
        if save:
            self._save_dashboard(fig, filename)
        
        return fig
    
    def create_policy_dashboard(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'policy_dashboard.html'
    ) -> go.Figure:
        """
        Create interactive policy analysis dashboard.
        
        Features: UI, retraining, subsidies, tax credits, policy effects.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            save: Whether to save the dashboard
            filename: Output filename
            
        Returns:
            Plotly Figure object
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'UI Participation',
                'Retraining Programs',
                'Wage Subsidy Spending',
                'Tax Credit Distribution'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'scatter'}],
                [{'type': 'scatter'}, {'type': 'scatter'}]
            ]
        )
        
        # UI recipients
        if 'ui_recipients' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['ui_recipients'],
                    mode='lines+markers',
                    name='UI Recipients',
                    line=dict(color='#e74c3c', width=2),
                    fill='tozeroy'
                ),
                row=1, col=1
            )
        
        # Retraining
        if 'retraining_active' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['retraining_active'],
                    mode='lines+markers',
                    name='Retraining',
                    line=dict(color='#3498db', width=2),
                    fill='tozeroy'
                ),
                row=1, col=2
            )
        
        # Wage subsidy spending
        if 'wage_subsidy_spending' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['wage_subsidy_spending'],
                    mode='lines+markers',
                    name='Subsidy Spend',
                    line=dict(color='#27ae60', width=2)
                ),
                row=2, col=1
            )
        
        # Tax credits
        if 'tax_credit_claims' in metrics_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=metrics_df['period'],
                    y=metrics_df['tax_credit_claims'],
                    mode='lines+markers',
                    name='Tax Credits',
                    line=dict(color='#f39c12', width=2)
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title_text="Policy Impact Dashboard",
            showlegend=False,
            height=self.config.height,
            template=self.config.template,
            hovermode='x unified'
        )
        
        if save:
            self._save_dashboard(fig, filename)
        
        return fig
    
    def create_scenario_comparison_dashboard(
        self,
        scenarios: Dict[str, pd.DataFrame],
        metric: str,
        metric_name: str,
        save: bool = True,
        filename: str = 'scenario_comparison.html'
    ) -> go.Figure:
        """
        Create scenario comparison dashboard.
        
        Args:
            scenarios: Dictionary mapping scenario names to metrics DataFrames
            metric: Column name to compare across scenarios
            metric_name: Display name for the metric
            save: Whether to save the dashboard
            filename: Output filename
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        colors = ['#3498db', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6']
        
        for i, (scenario_name, df) in enumerate(scenarios.items()):
            if metric in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['period'],
                        y=df[metric],
                        mode='lines+markers',
                        name=scenario_name,
                        line=dict(width=2.5, color=colors[i % len(colors)]),
                        marker=dict(size=6)
                    )
                )
        
        fig.update_layout(
            title_text=f"{metric_name} - Scenario Comparison",
            xaxis_title="Period (Quarters)",
            yaxis_title=metric_name,
            hovermode='x unified',
            height=self.config.height,
            template=self.config.template,
            legend=dict(x=0, y=1, bgcolor='rgba(255, 255, 255, 0.8)')
        )
        
        if save:
            self._save_dashboard(fig, filename)
        
        return fig
    
    def create_model_comparison_dashboard(
        self,
        baseline_df: pd.DataFrame,
        policy_df: pd.DataFrame,
        metric_columns: Optional[List[str]] = None,
        save: bool = True,
        filename: str = 'model_comparison.html'
    ) -> go.Figure:
        """
        Create side-by-side model comparison dashboard.
        
        Args:
            baseline_df: Baseline scenario metrics
            policy_df: Policy scenario metrics
            metric_columns: Specific metrics to compare. If None, uses common metrics.
            save: Whether to save the dashboard
            filename: Output filename
            
        Returns:
            Plotly Figure object
        """
        if metric_columns is None:
            # Find common metrics
            metric_columns = [
                col for col in baseline_df.columns
                if col in policy_df.columns and col != 'period'
            ][:4]  # Limit to 4 metrics for readability
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[f'{col.replace("_", " ").title()}' for col in metric_columns]
        )
        
        for idx, metric in enumerate(metric_columns):
            row = idx // 2 + 1
            col = idx % 2 + 1
            
            # Baseline
            fig.add_trace(
                go.Scatter(
                    x=baseline_df['period'],
                    y=baseline_df[metric],
                    mode='lines+markers',
                    name=f'{metric} (Baseline)',
                    line=dict(width=2, color='#3498db'),
                    marker=dict(size=5)
                ),
                row=row, col=col
            )
            
            # Policy
            fig.add_trace(
                go.Scatter(
                    x=policy_df['period'],
                    y=policy_df[metric],
                    mode='lines+markers',
                    name=f'{metric} (Policy)',
                    line=dict(width=2, color='#e74c3c', dash='dash'),
                    marker=dict(size=5, symbol='diamond')
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            title_text="Baseline vs Policy Scenarios",
            height=self.config.height + 100,
            template=self.config.template,
            hovermode='x unified',
            showlegend=True
        )
        
        if save:
            self._save_dashboard(fig, filename)
        
        return fig
    
    def _save_dashboard(self, fig: go.Figure, filename: str) -> Path:
        """
        Save dashboard to HTML file.
        
        Args:
            fig: Plotly Figure object
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_path = self.config.output_dir / filename
        fig.write_html(str(output_path))
        return output_path
    
    def generate_all_dashboards(
        self,
        metrics_df: pd.DataFrame,
        scenarios: Optional[Dict[str, pd.DataFrame]] = None,
        verbose: bool = True
    ) -> Dict[str, Path]:
        """
        Generate all available interactive dashboards.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            scenarios: Optional dictionary of scenario metrics for comparisons
            verbose: Whether to print progress
            
        Returns:
            Dictionary mapping dashboard names to output paths
        """
        dashboards = {}
        
        if verbose:
            print("Generating interactive dashboards...")
        
        # Core dashboards
        fig = self.create_overview_dashboard(metrics_df, save=True)
        dashboards['overview'] = self.config.output_dir / 'overview_dashboard.html'
        
        fig = self.create_labor_market_dashboard(metrics_df, save=True)
        dashboards['labor_market'] = self.config.output_dir / 'labor_market_dashboard.html'
        
        fig = self.create_technology_dashboard(metrics_df, save=True)
        dashboards['technology'] = self.config.output_dir / 'technology_dashboard.html'
        
        fig = self.create_inequality_dashboard(metrics_df, save=True)
        dashboards['inequality'] = self.config.output_dir / 'inequality_dashboard.html'
        
        # Conditional dashboards
        if 'num_firms' in metrics_df.columns:
            fig = self.create_firm_dynamics_dashboard(metrics_df, save=True)
            dashboards['firm_dynamics'] = self.config.output_dir / 'firm_dynamics_dashboard.html'
        
        if 'ui_recipients' in metrics_df.columns:
            fig = self.create_policy_dashboard(metrics_df, save=True)
            dashboards['policy'] = self.config.output_dir / 'policy_dashboard.html'
        
        # Scenario comparisons
        if scenarios is not None:
            for metric in ['unemployment_rate', 'avg_wage_human', 'ai_employment_share']:
                if metric in metrics_df.columns:
                    scenario_dict = {
                        name: df for name, df in scenarios.items()
                        if metric in df.columns
                    }
                    if scenario_dict:
                        fig = self.create_scenario_comparison_dashboard(
                            scenario_dict,
                            metric,
                            metric.replace('_', ' ').title(),
                            save=True
                        )
                        dashboards[f'scenario_{metric}'] = self.config.output_dir / f'scenario_comparison_{metric}.html'
        
        if verbose:
            print(f"Generated {len(dashboards)} interactive dashboards")
            for name, path in dashboards.items():
                print(f"  ✓ {name}: {path}")
        
        return dashboards
