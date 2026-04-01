"""
Phase 8: Benchmark scenario runners for standardized simulations.

Provides predefined scenarios for comparing simulation outcomes:
- Baseline: Default parameters, no policy
- High AI: Accelerated AI adoption
- Policy: Intervention programs active
- Sectoral Shift: Unequal AI exposure

Classes:
    BenchmarkScenario: Individual scenario definition
    BenchmarkRunner: Orchestrates scenario execution
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

from src.config.parameters import SimulationConfig, DEFAULT_CONFIG
from src.simulation.engine import SimulationEngine


@dataclass
class BenchmarkScenario:
    """Definition of a benchmark scenario."""
    name: str
    description: str
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    num_periods: int = 240  # 20 years * 12 months
    num_runs: int = 1  # Number of replications
    random_seed: Optional[int] = None
    
    def get_config(self, base_config: SimulationConfig) -> SimulationConfig:
        """
        Get simulation config for this scenario.
        
        Args:
            base_config: Base configuration to modify
            
        Returns:
            Modified SimulationConfig
        """
        # Create a copy via dict manipulation
        config_dict = base_config.model_dump()
        config_dict.update(self.config_overrides)
        return SimulationConfig(**config_dict)


class BenchmarkRunner:
    """Orchestrate and execute benchmark scenarios."""
    
    # Predefined scenarios
    BASELINE = BenchmarkScenario(
        name="Baseline",
        description="Default parameters, no policy interventions",
        config_overrides={
            # Use default config as-is
        },
        num_periods=240,
        random_seed=42
    )
    
    HIGH_AI = BenchmarkScenario(
        name="High AI",
        description="Accelerated AI adoption with higher productivity",
        config_overrides={
            'ai_productivity_multiplier': 2.0,  # vs 1.5x default
            'ai_wage_ratio': 0.3,  # vs 0.5x default
        },
        num_periods=240,
        random_seed=42
    )
    
    POLICY = BenchmarkScenario(
        name="Policy",
        description="Active policy interventions: UI, retraining, subsidies",
        config_overrides={
            # Use default config - policies handled at agent level
        },
        num_periods=240,
        random_seed=42
    )
    
    SECTORAL_SHIFT = BenchmarkScenario(
        name="Sectoral Shift",
        description="Unequal AI exposure across job categories",
        config_overrides={
            'num_firms': 5,  # More firms for sectoral diversity
        },
        num_periods=240,
        random_seed=42
    )
    
    NO_AI = BenchmarkScenario(
        name="No AI",
        description="Counterfactual: Low AI productivity",
        config_overrides={
            'ai_productivity_multiplier': 0.8,  # AI less productive
            'ai_wage_ratio': 2.0,  # AI more expensive
        },
        num_periods=240,
        random_seed=42
    )
    
    POLICY_PLUS_AI = BenchmarkScenario(
        name="Policy + High AI",
        description="Combined: high AI productivity + more firms",
        config_overrides={
            'ai_productivity_multiplier': 2.0,
            'ai_wage_ratio': 0.3,
            'num_firms': 5,
        },
        num_periods=240,
        random_seed=42
    )
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        verbose: bool = True
    ):
        """
        Initialize benchmark runner.
        
        Args:
            output_dir: Directory to save results. If None, uses 'outputs/benchmarks'
            verbose: Whether to print progress
        """
        if output_dir is None:
            output_dir = Path('outputs/benchmarks')
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.results: Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]] = {}
    
    def run_scenario(
        self,
        scenario: BenchmarkScenario,
        base_config: Optional[SimulationConfig] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Run a single benchmark scenario.
        
        Args:
            scenario: BenchmarkScenario to execute
            base_config: Base configuration to start from
            
        Returns:
            Tuple of (metrics_dataframe, summary_statistics)
        """
        if base_config is None:
            base_config = DEFAULT_CONFIG
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Running: {scenario.name}")
            print(f"Description: {scenario.description}")
            print(f"Periods: {scenario.num_periods}")
            print(f"Runs: {scenario.num_runs}")
            print(f"{'='*60}")
        
        # Get scenario config
        config = scenario.get_config(base_config)
        
        # Run simulation(s)
        all_metrics = []
        
        for run_num in range(scenario.num_runs):
            if scenario.num_runs > 1 and self.verbose:
                print(f"  Run {run_num + 1}/{scenario.num_runs}...", end='', flush=True)
            
            # Set random seed if provided
            if scenario.random_seed is not None:
                np.random.seed(scenario.random_seed + run_num)
            
            # Run simulation
            engine = SimulationEngine(config)
            metrics_list = []
            
            for period in range(scenario.num_periods):
                engine.step()
                stats = engine.get_aggregate_statistics()
                stats['period'] = period
                metrics_list.append(stats)
            
            metrics_df = pd.DataFrame(metrics_list)
            all_metrics.append(metrics_df)
            
            if scenario.num_runs > 1 and self.verbose:
                print(" done")
        
        # Aggregate across runs (if multiple)
        if scenario.num_runs > 1:
            # Average metrics across runs
            metrics_df = pd.concat(all_metrics).groupby('period').mean().reset_index()
        else:
            metrics_df = all_metrics[0]
        
        # Calculate summary statistics
        summary = self._calculate_summary(metrics_df, scenario)
        
        # Store results
        self.results[scenario.name] = (metrics_df, summary)
        
        # Save to disk
        self._save_results(scenario, metrics_df, summary)
        
        if self.verbose:
            self._print_summary(scenario.name, summary)
        
        return metrics_df, summary
    
    def run_all_default_scenarios(
        self,
        base_config: Optional[SimulationConfig] = None
    ) -> Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]]:
        """
        Run all default benchmark scenarios.
        
        Args:
            base_config: Base configuration to start from
            
        Returns:
            Dictionary mapping scenario names to (metrics_df, summary) tuples
        """
        scenarios = [
            self.BASELINE,
            self.HIGH_AI,
            self.POLICY,
            self.SECTORAL_SHIFT,
            self.NO_AI,
            self.POLICY_PLUS_AI,
        ]
        
        for scenario in scenarios:
            self.run_scenario(scenario, base_config)
        
        return self.results
    
    def run_custom_scenarios(
        self,
        scenarios: List[BenchmarkScenario],
        base_config: Optional[SimulationConfig] = None
    ) -> Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]]:
        """
        Run a custom list of scenarios.
        
        Args:
            scenarios: List of BenchmarkScenario objects
            base_config: Base configuration to start from
            
        Returns:
            Dictionary mapping scenario names to (metrics_df, summary) tuples
        """
        for scenario in scenarios:
            self.run_scenario(scenario, base_config)
        
        return self.results
    
    def _calculate_summary(
        self,
        metrics_df: pd.DataFrame,
        scenario: BenchmarkScenario
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for a scenario.
        
        Args:
            metrics_df: Metrics DataFrame
            scenario: BenchmarkScenario object
            
        Returns:
            Dictionary of summary statistics
        """
        summary = {
            'scenario_name': scenario.name,
            'num_periods': len(metrics_df),
            'runtime_datetime': datetime.now().isoformat(),
        }
        
        # Labor market metrics
        if 'unemployment_rate' in metrics_df.columns:
            summary['unemployment_mean'] = float(metrics_df['unemployment_rate'].mean())
            summary['unemployment_std'] = float(metrics_df['unemployment_rate'].std())
            summary['unemployment_min'] = float(metrics_df['unemployment_rate'].min())
            summary['unemployment_max'] = float(metrics_df['unemployment_rate'].max())
        
        # Check for wage column (could be 'avg_wage_human' or 'market_wage_human')
        wage_col = None
        if 'avg_wage_human' in metrics_df.columns:
            wage_col = 'avg_wage_human'
        elif 'market_wage_human' in metrics_df.columns:
            wage_col = 'market_wage_human'
        
        if wage_col:
            wages = metrics_df[wage_col]
            summary['wage_initial'] = float(wages.iloc[0])
            summary['wage_final'] = float(wages.iloc[-1])
            summary['wage_growth_pct'] = float((wages.iloc[-1] / wages.iloc[0] - 1) * 100) if wages.iloc[0] > 0 else 0.0
        
        # AI metrics
        if 'ai_employment_share' in metrics_df.columns:
            ai_share = metrics_df['ai_employment_share']
            summary['ai_share_initial'] = float(ai_share.iloc[0])
            summary['ai_share_final'] = float(ai_share.iloc[-1])
        
        if 'total_r_and_d_spending' in metrics_df.columns:
            summary['rd_spending_total'] = float(metrics_df['total_r_and_d_spending'].iloc[-1])
        
        # Inequality metrics
        if 'gini_coefficient' in metrics_df.columns:
            gini = metrics_df['gini_coefficient']
            summary['gini_mean'] = float(gini.mean())
            summary['gini_change'] = float(gini.iloc[-1] - gini.iloc[0])
        
        if 'wage_gap_ratio' in metrics_df.columns:
            gap = metrics_df['wage_gap_ratio']
            summary['wage_gap_initial'] = float(gap.iloc[0])
            summary['wage_gap_final'] = float(gap.iloc[-1])
            summary['wage_gap_change'] = float(gap.iloc[-1] - gap.iloc[0])
        
        # Firm metrics
        if 'num_firms' in metrics_df.columns:
            summary['num_firms_initial'] = int(metrics_df['num_firms'].iloc[0])
            summary['num_firms_final'] = int(metrics_df['num_firms'].iloc[-1])
        
        return summary
    
    def _save_results(
        self,
        scenario: BenchmarkScenario,
        metrics_df: pd.DataFrame,
        summary: Dict[str, Any]
    ) -> None:
        """
        Save results to disk.
        
        Args:
            scenario: BenchmarkScenario object
            metrics_df: Metrics DataFrame
            summary: Summary statistics
        """
        # Create scenario subdirectory
        scenario_dir = self.output_dir / scenario.name.lower().replace(' ', '_')
        scenario_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metrics as CSV
        metrics_path = scenario_dir / 'metrics.csv'
        metrics_df.to_csv(metrics_path, index=False)
        
        # Save summary as CSV (single row)
        summary_df = pd.DataFrame([summary])
        summary_path = scenario_dir / 'summary.csv'
        summary_df.to_csv(summary_path, index=False)
    
    def _print_summary(self, scenario_name: str, summary: Dict[str, Any]) -> None:
        """Print summary statistics."""
        print(f"\n{scenario_name} Summary:")
        print("-" * 40)
        
        key_metrics = [
            'unemployment_mean',
            'wage_growth_pct',
            'ai_share_final',
            'gini_change',
            'wage_gap_change'
        ]
        
        for key in key_metrics:
            if key in summary:
                value = summary[key]
                if isinstance(value, float):
                    if 'pct' in key or 'rate' in key.lower():
                        print(f"  {key}: {value:.2f}%")
                    elif 'wage_gap' in key or 'gini' in key:
                        print(f"  {key}: {value:.4f}")
                    else:
                        print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
    
    def compare_scenarios(
        self,
        scenario_names: Optional[List[str]] = None,
        save: bool = True
    ) -> pd.DataFrame:
        """
        Compare summary statistics across scenarios.
        
        Args:
            scenario_names: Specific scenarios to compare. If None, uses all.
            save: Whether to save comparison to disk
            
        Returns:
            DataFrame with comparison
        """
        if scenario_names is None:
            scenario_names = list(self.results.keys())
        
        # Extract summaries
        summaries = []
        for name in scenario_names:
            if name in self.results:
                _, summary = self.results[name]
                summaries.append(summary)
        
        comparison_df = pd.DataFrame(summaries)
        
        if save:
            comparison_path = self.output_dir / 'scenario_comparison.csv'
            comparison_df.to_csv(comparison_path, index=False)
            if self.verbose:
                print(f"Comparison saved to {comparison_path}")
        
        return comparison_df
    
    def get_results(self) -> Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]]:
        """Get all results."""
        return self.results
    
    def get_metrics_df(self, scenario_name: str) -> Optional[pd.DataFrame]:
        """Get metrics DataFrame for a scenario."""
        if scenario_name in self.results:
            return self.results[scenario_name][0]
        return None
    
    def get_summary(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Get summary for a scenario."""
        if scenario_name in self.results:
            return self.results[scenario_name][1]
        return None
