"""
Phase 7: Static visualization module for simulation results analysis.

This module provides comprehensive plotting functions for analyzing simulation outputs
across labor market, technology, firm dynamics, and policy dimensions.

Classes:
    PlotGenerator: Main class for generating all plot types
    PlotConfig: Configuration for plot styling and export settings
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime


@dataclass
class PlotConfig:
    """Configuration for plots: styling, colors, sizes."""
    
    # General settings
    figure_size: Tuple[int, int] = (12, 6)
    large_figure_size: Tuple[int, int] = (14, 8)
    dpi: int = 300
    style: str = "darkgrid"
    
    # Color palettes
    palette_skill: Dict[str, str] = None
    palette_category: Dict[str, str] = None
    palette_scenario: Dict[str, str] = None
    
    # Font settings
    title_size: int = 14
    label_size: int = 11
    tick_size: int = 10
    
    # Output
    output_dir: Path = None
    format: str = "png"  # png, pdf, eps
    
    def __post_init__(self):
        """Set defaults for color palettes."""
        if self.palette_skill is None:
            self.palette_skill = {
                'low': '#e74c3c',      # Red
                'high': '#27ae60',     # Green
                'aggregate': '#3498db' # Blue
            }
        
        if self.palette_category is None:
            self.palette_category = {
                'Routine': '#e74c3c',
                'Management': '#f39c12',
                'Creative': '#27ae60'
            }
        
        if self.palette_scenario is None:
            self.palette_scenario = {
                'Baseline': '#3498db',
                'High AI': '#e74c3c',
                'Policy': '#27ae60',
                'Baseline': '#95a5a6'
            }
        
        if self.output_dir is None:
            self.output_dir = Path('outputs/plots')
        self.output_dir.mkdir(parents=True, exist_ok=True)


class PlotGenerator:
    """Generate publication-ready plots from simulation metrics."""
    
    def __init__(self, config: Optional[PlotConfig] = None):
        """
        Initialize the plot generator.
        
        Args:
            config: PlotConfig instance for styling. If None, uses defaults.
        """
        self.config = config or PlotConfig()
        sns.set_style(self.config.style)
        plt.rcParams['figure.figsize'] = self.config.figure_size
        plt.rcParams['font.size'] = self.config.label_size
    
    def plot_unemployment_timeseries(
        self, 
        metrics_df: pd.DataFrame,
        include_skill_breakdown: bool = True,
        save: bool = True,
        filename: str = 'unemployment_timeseries.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot unemployment rate over time.
        
        Args:
            metrics_df: DataFrame with period, unemployment_rate, and optional
                       unemployment_rate_low_skill, unemployment_rate_high_skill columns
            include_skill_breakdown: Whether to show skill-level breakdown
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        # Aggregate unemployment
        ax.plot(metrics_df['period'], metrics_df['unemployment_rate'], 
               linewidth=2.5, label='Overall', color=self.config.palette_skill['aggregate'],
               marker='o', markersize=4)
        
        # Skill breakdown if available
        if include_skill_breakdown:
            if 'unemployment_rate_low_skill' in metrics_df.columns:
                ax.plot(metrics_df['period'], metrics_df['unemployment_rate_low_skill'],
                       linewidth=2, label='Low-Skill', color=self.config.palette_skill['low'],
                       linestyle='--', alpha=0.8)
            
            if 'unemployment_rate_high_skill' in metrics_df.columns:
                ax.plot(metrics_df['period'], metrics_df['unemployment_rate_high_skill'],
                       linewidth=2, label='High-Skill', color=self.config.palette_skill['high'],
                       linestyle='--', alpha=0.8)
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel('Unemployment Rate', fontsize=self.config.label_size)
        ax.set_title('Unemployment Rate Over Time', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def plot_wage_evolution(
        self,
        metrics_df: pd.DataFrame,
        include_skill_breakdown: bool = True,
        save: bool = True,
        filename: str = 'wage_evolution.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot wage levels over time.
        
        Args:
            metrics_df: DataFrame with period and wage columns
            include_skill_breakdown: Whether to show by skill level
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        # Aggregate wage
        if 'avg_wage_human' in metrics_df.columns:
            ax.plot(metrics_df['period'], metrics_df['avg_wage_human'],
                   linewidth=2.5, label='Human Workers', 
                   color=self.config.palette_skill['aggregate'],
                   marker='o', markersize=4)
        
        # AI wage if available
        if 'avg_wage_ai' in metrics_df.columns:
            ax.plot(metrics_df['period'], metrics_df['avg_wage_ai'],
                   linewidth=2.5, label='AI Cost', color='#9b59b6',
                   marker='s', markersize=4)
        
        # Skill breakdown
        if include_skill_breakdown:
            if 'avg_wage_low_skill' in metrics_df.columns:
                ax.plot(metrics_df['period'], metrics_df['avg_wage_low_skill'],
                       linewidth=2, label='Low-Skill', color=self.config.palette_skill['low'],
                       linestyle='--', alpha=0.8)
            
            if 'avg_wage_high_skill' in metrics_df.columns:
                ax.plot(metrics_df['period'], metrics_df['avg_wage_high_skill'],
                       linewidth=2, label='High-Skill', color=self.config.palette_skill['high'],
                       linestyle='--', alpha=0.8)
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel('Average Wage ($)', fontsize=self.config.label_size)
        ax.set_title('Wage Evolution Over Time', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def plot_ai_adoption(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'ai_adoption.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot AI adoption rate over time.
        
        Args:
            metrics_df: DataFrame with AI adoption metrics
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        # Overall AI employment share
        if 'ai_employment_share' in metrics_df.columns:
            ax.plot(metrics_df['period'], metrics_df['ai_employment_share'],
                   linewidth=2.5, label='AI Employment Share',
                   color='#9b59b6', marker='o', markersize=4)
        
        # AI adoption by category if available
        for category in ['Routine', 'Management', 'Creative']:
            col = f'ai_adoption_{category.lower()}'
            if col in metrics_df.columns:
                ax.plot(metrics_df['period'], metrics_df[col],
                       linewidth=2, label=f'{category}',
                       color=self.config.palette_category[category],
                       linestyle='--', alpha=0.8)
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel('AI Adoption Rate', fontsize=self.config.label_size)
        ax.set_title('AI Adoption Over Time', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def plot_rd_spending(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'rd_spending.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot R&D spending over time.
        
        Args:
            metrics_df: DataFrame with R&D metrics
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        if 'total_r_and_d_spending' in metrics_df.columns:
            ax.plot(metrics_df['period'], metrics_df['total_r_and_d_spending'],
                   linewidth=2.5, label='Total R&D Spending',
                   color='#e67e22', marker='o', markersize=4)
        
        # R&D by category if available
        for category in ['Routine', 'Management', 'Creative']:
            col = f'r_and_d_spending_{category.lower()}'
            if col in metrics_df.columns:
                ax.plot(metrics_df['period'], metrics_df[col],
                       linewidth=2, label=f'R&D {category}',
                       color=self.config.palette_category[category],
                       linestyle='--', alpha=0.8)
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel('R&D Spending ($)', fontsize=self.config.label_size)
        ax.set_title('R&D Spending Over Time', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def plot_wage_distribution(
        self,
        wages: np.ndarray,
        title: str = 'Wage Distribution',
        save: bool = True,
        filename: str = 'wage_distribution.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot wage distribution with histogram and violin plot.
        
        Args:
            wages: Array of wages
            title: Plot title
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, axes = plt.subplots(1, 2, figsize=self.config.large_figure_size)
        
        # Histogram
        axes[0].hist(wages, bins=50, color=self.config.palette_skill['aggregate'],
                    alpha=0.7, edgecolor='black')
        axes[0].set_xlabel('Wage ($)', fontsize=self.config.label_size)
        axes[0].set_ylabel('Frequency', fontsize=self.config.label_size)
        axes[0].set_title('Histogram', fontsize=self.config.label_size)
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Violin plot
        axes[1].violinplot([wages], positions=[0], widths=0.7, showmeans=True, showmedians=True)
        axes[1].set_ylabel('Wage ($)', fontsize=self.config.label_size)
        axes[1].set_title('Distribution', fontsize=self.config.label_size)
        axes[1].set_xticks([0])
        axes[1].set_xticklabels(['All Workers'])
        axes[1].grid(True, alpha=0.3, axis='y')
        
        fig.suptitle(title, fontsize=self.config.title_size, fontweight='bold')
        plt.tight_layout()
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, axes
    
    def plot_wage_inequality(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'wage_inequality.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot wage inequality indices over time.
        
        Args:
            metrics_df: DataFrame with inequality metrics
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        # Gini coefficient
        if 'gini_coefficient' in metrics_df.columns:
            ax.plot(metrics_df['period'], metrics_df['gini_coefficient'],
                   linewidth=2.5, label='Gini Coefficient',
                   color=self.config.palette_skill['aggregate'],
                   marker='o', markersize=4)
        
        # Theil index if available
        if 'theil_index' in metrics_df.columns:
            ax2 = ax.twinx()
            ax2.plot(metrics_df['period'], metrics_df['theil_index'],
                    linewidth=2.5, label='Theil Index',
                    color='#e74c3c', marker='s', markersize=4)
            ax2.set_ylabel('Theil Index', fontsize=self.config.label_size, color='#e74c3c')
            ax2.tick_params(axis='y', labelcolor='#e74c3c')
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel('Gini Coefficient', fontsize=self.config.label_size)
        ax.set_title('Wage Inequality Over Time', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='upper left', framealpha=0.9)
        if 'theil_index' in metrics_df.columns:
            ax2.legend(loc='upper right', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def plot_wage_gap(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'wage_gap.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot wage gap (high-skill / low-skill ratio) over time.
        
        Args:
            metrics_df: DataFrame with wage gap metrics
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        if 'wage_gap_ratio' in metrics_df.columns:
            ax.plot(metrics_df['period'], metrics_df['wage_gap_ratio'],
                   linewidth=2.5, label='High-Skill / Low-Skill Wage Ratio',
                   color=self.config.palette_skill['aggregate'],
                   marker='o', markersize=4, markerfacecolor='white', markeredgewidth=2)
        
        # Add reference line
        ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Parity')
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel('Wage Ratio', fontsize=self.config.label_size)
        ax.set_title('Wage Gap Evolution (Polarization)', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def plot_scenario_comparison(
        self,
        scenarios_dict: Dict[str, pd.DataFrame],
        metric: str,
        metric_label: str,
        save: bool = True,
        filename: str = 'scenario_comparison.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot comparison of multiple scenarios for a given metric.
        
        Args:
            scenarios_dict: Dictionary mapping scenario names to metrics DataFrames
            metric: Column name in DataFrames to plot
            metric_label: Label for the metric (for axis)
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        colors = list(self.config.palette_scenario.values())
        for i, (scenario_name, df) in enumerate(scenarios_dict.items()):
            if metric in df.columns:
                color = colors[i % len(colors)]
                ax.plot(df['period'], df[metric], linewidth=2.5, label=scenario_name,
                       marker='o', markersize=4, color=color)
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel(metric_label, fontsize=self.config.label_size)
        ax.set_title(f'{metric_label} Across Scenarios', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def plot_firm_size_distribution(
        self,
        firm_sizes: np.ndarray,
        title: str = 'Firm Size Distribution',
        save: bool = True,
        filename: str = 'firm_size_distribution.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot firm size distribution with log scale.
        
        Args:
            firm_sizes: Array of firm sizes (employment)
            title: Plot title
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, axes = plt.subplots(1, 2, figsize=self.config.large_figure_size)
        
        # Linear histogram
        axes[0].hist(firm_sizes, bins=30, color=self.config.palette_skill['aggregate'],
                    alpha=0.7, edgecolor='black')
        axes[0].set_xlabel('Firm Size (Employees)', fontsize=self.config.label_size)
        axes[0].set_ylabel('Frequency', fontsize=self.config.label_size)
        axes[0].set_title('Linear Scale', fontsize=self.config.label_size)
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Log scale
        axes[1].hist(firm_sizes, bins=30, color=self.config.palette_skill['aggregate'],
                    alpha=0.7, edgecolor='black')
        axes[1].set_xlabel('Firm Size (Employees)', fontsize=self.config.label_size)
        axes[1].set_ylabel('Frequency (log scale)', fontsize=self.config.label_size)
        axes[1].set_title('Log Scale', fontsize=self.config.label_size)
        axes[1].set_yscale('log')
        axes[1].grid(True, alpha=0.3, which='both')
        
        fig.suptitle(title, fontsize=self.config.title_size, fontweight='bold')
        plt.tight_layout()
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, axes
    
    def plot_employment_by_category(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'employment_by_category.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot employment composition by job category.
        
        Args:
            metrics_df: DataFrame with employment by category
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        # Employment levels by category
        categories = ['Routine', 'Management', 'Creative']
        category_data = {}
        
        for category in categories:
            col = f'employment_{category.lower()}'
            if col in metrics_df.columns:
                category_data[category] = metrics_df[col]
        
        if category_data:
            df_plot = pd.DataFrame(category_data)
            for category, color in self.config.palette_category.items():
                if category in df_plot.columns:
                    ax.plot(metrics_df['period'], df_plot[category],
                           linewidth=2, label=category, color=color, marker='o', markersize=4)
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel('Employment', fontsize=self.config.label_size)
        ax.set_title('Employment by Job Category', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def plot_productivity_growth(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'productivity_growth.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot productivity growth over time.
        
        Args:
            metrics_df: DataFrame with productivity metrics
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        # Output per worker
        if 'output_per_worker' in metrics_df.columns:
            ax.plot(metrics_df['period'], metrics_df['output_per_worker'],
                   linewidth=2.5, label='Output per Worker',
                   color=self.config.palette_skill['aggregate'],
                   marker='o', markersize=4)
        
        # Human productivity if available
        if 'human_avg_productivity' in metrics_df.columns:
            ax.plot(metrics_df['period'], metrics_df['human_avg_productivity'],
                   linewidth=2, label='Human Productivity',
                   color=self.config.palette_skill['high'], linestyle='--', alpha=0.8)
        
        # AI productivity if available
        if 'ai_avg_productivity' in metrics_df.columns:
            ax.plot(metrics_df['period'], metrics_df['ai_avg_productivity'],
                   linewidth=2, label='AI Productivity',
                   color='#9b59b6', linestyle='--', alpha=0.8)
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel('Productivity', fontsize=self.config.label_size)
        ax.set_title('Productivity Growth', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def plot_policy_impact(
        self,
        metrics_df: pd.DataFrame,
        save: bool = True,
        filename: str = 'policy_impact.png'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot policy program impacts on unemployment.
        
        Args:
            metrics_df: DataFrame with policy metrics
            save: Whether to save the figure
            filename: Output filename
            
        Returns:
            Tuple of (Figure, Axes)
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)
        
        # UI recipients
        if 'ui_recipients' in metrics_df.columns:
            ax.bar(metrics_df['period'], metrics_df['ui_recipients'],
                  label='UI Recipients', alpha=0.7, color=self.config.palette_skill['aggregate'])
        
        # Retraining active
        if 'retraining_active' in metrics_df.columns:
            ax.bar(metrics_df['period'], metrics_df['retraining_active'],
                  label='Retraining Participants', alpha=0.7, bottom=metrics_df.get('ui_recipients', 0),
                  color=self.config.palette_skill['high'])
        
        ax.set_xlabel('Period (Quarters)', fontsize=self.config.label_size)
        ax.set_ylabel('Number of Recipients', fontsize=self.config.label_size)
        ax.set_title('Policy Program Participation', fontsize=self.config.title_size, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(bottom=0)
        
        if save:
            self._save_figure(fig, filename)
        
        return fig, ax
    
    def _save_figure(self, fig: plt.Figure, filename: str) -> Path:
        """
        Save figure to output directory.
        
        Args:
            fig: Matplotlib figure
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_path = self.config.output_dir / filename
        fig.savefig(output_path, dpi=self.config.dpi, bbox_inches='tight', format=self.config.format)
        plt.close(fig)
        return output_path
    
    def generate_all_plots(
        self,
        metrics_df: pd.DataFrame,
        wages: Optional[np.ndarray] = None,
        firm_sizes: Optional[np.ndarray] = None,
        verbose: bool = True
    ) -> Dict[str, Path]:
        """
        Generate all available plots from metrics data.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            wages: Optional array of wages for distribution plots
            firm_sizes: Optional array of firm sizes
            verbose: Whether to print progress
            
        Returns:
            Dictionary mapping plot names to output paths
        """
        plots = {}
        
        # Time series plots
        if verbose:
            print("Generating time series plots...")
        
        fig, ax = self.plot_unemployment_timeseries(metrics_df, save=True)
        plt.close(fig)
        plots['unemployment'] = self.config.output_dir / 'unemployment_timeseries.png'
        
        fig, ax = self.plot_wage_evolution(metrics_df, save=True)
        plt.close(fig)
        plots['wages'] = self.config.output_dir / 'wage_evolution.png'
        
        fig, ax = self.plot_ai_adoption(metrics_df, save=True)
        plt.close(fig)
        plots['ai_adoption'] = self.config.output_dir / 'ai_adoption.png'
        
        fig, ax = self.plot_rd_spending(metrics_df, save=True)
        plt.close(fig)
        plots['rd_spending'] = self.config.output_dir / 'rd_spending.png'
        
        # Distribution plots
        if verbose:
            print("Generating distribution plots...")
        
        if wages is not None:
            fig, axes = self.plot_wage_distribution(wages, save=True)
            plt.close(fig)
            plots['wage_distribution'] = self.config.output_dir / 'wage_distribution.png'
        
        if firm_sizes is not None:
            fig, axes = self.plot_firm_size_distribution(firm_sizes, save=True)
            plt.close(fig)
            plots['firm_size_distribution'] = self.config.output_dir / 'firm_size_distribution.png'
        
        # Inequality plots
        if verbose:
            print("Generating inequality plots...")
        
        fig, ax = self.plot_wage_inequality(metrics_df, save=True)
        plt.close(fig)
        plots['inequality'] = self.config.output_dir / 'wage_inequality.png'
        
        fig, ax = self.plot_wage_gap(metrics_df, save=True)
        plt.close(fig)
        plots['wage_gap'] = self.config.output_dir / 'wage_gap.png'
        
        # Other economic plots
        if verbose:
            print("Generating economic plots...")
        
        if any(col.startswith('employment_') for col in metrics_df.columns):
            fig, ax = self.plot_employment_by_category(metrics_df, save=True)
            plt.close(fig)
            plots['employment'] = self.config.output_dir / 'employment_by_category.png'
        
        if 'output_per_worker' in metrics_df.columns:
            fig, ax = self.plot_productivity_growth(metrics_df, save=True)
            plt.close(fig)
            plots['productivity'] = self.config.output_dir / 'productivity_growth.png'
        
        if 'ui_recipients' in metrics_df.columns or 'retraining_active' in metrics_df.columns:
            fig, ax = self.plot_policy_impact(metrics_df, save=True)
            plt.close(fig)
            plots['policy'] = self.config.output_dir / 'policy_impact.png'
        
        if verbose:
            print(f"Generated {len(plots)} plots")
            for name, path in plots.items():
                print(f"  ✓ {name}: {path}")
        
        return plots
