"""
Comprehensive Metrics & Analytics Module (Phase 6)

Extends metrics collection for deep economic analysis:
- 30+ metrics covering labor, technology, inequality, and policy effects
- Inequality indices (Gini, Theil, wage polarization)
- Sectoral metrics by job category
- Export functionality (CSV, Parquet)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class PeriodMetrics:
    """Comprehensive metrics for each simulation period."""
    
    # ========== Identification ==========
    period: int
    
    # ========== Labor Market Metrics ==========
    num_employed_human: int
    num_employed_ai: int
    num_unemployed: int
    unemployment_rate: float
    labor_force: int
    
    # ========== Wage Metrics ==========
    avg_wage_human: float
    median_wage_human: float
    wage_std_human: float
    min_wage: float
    max_wage: float
    
    # ========== Output & Productivity ==========
    total_output: float
    output_per_worker: float
    output_per_human_worker: float
    output_per_ai_worker: float
    
    # ========== Firm Metrics ==========
    num_firms: int
    avg_firm_size: float
    total_firm_profits: float
    avg_firm_profit: float
    num_firms_positive_profit: int
    
    # ========== Matching Metrics ==========
    job_vacancies: int
    job_matches: int
    job_match_rate: float
    
    # ========== Entry/Exit ==========
    new_firms_entered: int
    firms_exited: int
    firm_entry_rate: float
    firm_exit_rate: float
    
    # ========== AI Adoption Metrics ==========
    ai_employment_share: float
    cumulative_ai_adopted: int
    ai_adoption_rate: float  # periods/innovation
    
    # ========== R&D Metrics ==========
    total_r_and_d_spending: float
    avg_r_and_d_by_firm: float
    r_and_d_as_share_of_output: float
    
    # ========== Inequality Metrics ==========
    gini_coefficient: float
    theil_index: float
    wage_gap_ratio: float  # High-skill / Low-skill
    employment_concentration: float
    
    # ========== Skill-Based Metrics ==========
    low_skill_unemployment: float = 0.0
    high_skill_unemployment: float = 0.0
    low_skill_avg_wage: float = 0.0
    high_skill_avg_wage: float = 0.0
    
    # ========== Sectoral Metrics ==========
    routine_employment_share: float = 0.0
    management_employment_share: float = 0.0
    creative_employment_share: float = 0.0
    
    # ========== Policy Metrics ==========
    ui_recipients: int = 0
    ui_spending: float = 0.0
    retraining_graduates: int = 0
    retraining_spending: float = 0.0
    wage_subsidy_spending: float = 0.0
    
    # ========== Miscellaneous ==========
    avg_reservation_wage: float = 0.0
    labor_market_tightness: float = 0.0  # Vacancies / Unemployment
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class MetricsCalculator:
    """Calculates comprehensive metrics from simulation state."""
    
    @staticmethod
    def calculate_gini(wages: List[float]) -> float:
        """Calculate Gini coefficient for wage distribution."""
        if not wages or len(wages) < 2:
            return 0.0
        
        sorted_wages = sorted(wages)
        n = len(sorted_wages)
        cumsum = sum(i * w for i, w in enumerate(sorted_wages, 1))
        
        return (2 * cumsum) / (n * sum(sorted_wages)) - (n + 1) / n if sum(sorted_wages) > 0 else 0.0
    
    @staticmethod
    def calculate_theil(wages: List[float], mean_wage: float) -> float:
        """Calculate Theil index for wage inequality."""
        if not wages or mean_wage <= 0:
            return 0.0
        
        n = len(wages)
        if n == 0:
            return 0.0
        
        theil = 0.0
        for wage in wages:
            if wage > 0:
                theil += (wage / mean_wage) * math.log(wage / mean_wage)
        
        return theil / n if n > 0 else 0.0
    
    @staticmethod
    def calculate_herfindahl(firm_sizes: List[int], total_employment: int) -> float:
        """Calculate Herfindahl index for employment concentration."""
        if not firm_sizes or total_employment == 0:
            return 0.0
        
        herfindahl = sum((size / total_employment) ** 2 for size in firm_sizes)
        return herfindahl
    
    @staticmethod
    def calculate_wage_gap_ratio(low_skill_wages: List[float], 
                                 high_skill_wages: List[float]) -> float:
        """Calculate high-skill to low-skill wage ratio."""
        low_avg = sum(low_skill_wages) / len(low_skill_wages) if low_skill_wages else 1.0
        high_avg = sum(high_skill_wages) / len(high_skill_wages) if high_skill_wages else 1.0
        
        return high_avg / low_avg if low_avg > 0 else 1.0


class MetricsTracker:
    """Tracks metrics throughout simulation."""
    
    def __init__(self):
        self.period_metrics: List[PeriodMetrics] = []
        self.current_period: Optional[PeriodMetrics] = None
    
    def add_period_metrics(self, metrics: PeriodMetrics):
        """Record metrics for a period."""
        self.period_metrics.append(metrics)
        self.current_period = metrics
    
    def get_period(self, period: int) -> Optional[PeriodMetrics]:
        """Get metrics for specific period."""
        for m in self.period_metrics:
            if m.period == period:
                return m
        return None
    
    def get_metric_series(self, metric_name: str) -> List[Tuple[int, float]]:
        """Get time series of metric as (period, value) tuples."""
        series = []
        for m in self.period_metrics:
            value = getattr(m, metric_name, None)
            if value is not None:
                series.append((m.period, value))
        return series
    
    def calculate_average(self, metric_name: str) -> float:
        """Calculate average across all periods."""
        values = [m[1] for m in self.get_metric_series(metric_name)]
        return sum(values) / len(values) if values else 0.0
    
    def calculate_trend(self, metric_name: str) -> float:
        """Calculate linear trend (slope) of metric over time."""
        series = self.get_metric_series(metric_name)
        if len(series) < 2:
            return 0.0
        
        n = len(series)
        periods = [p for p, _ in series]
        values = [v for _, v in series]
        
        # Linear regression: slope = (n*Σpv - Σp*Σv) / (n*Σp² - (Σp)²)
        sum_pv = sum(p * v for p, v in zip(periods, values))
        sum_p = sum(periods)
        sum_v = sum(values)
        sum_p2 = sum(p ** 2 for p in periods)
        
        denominator = n * sum_p2 - sum_p ** 2
        if denominator == 0:
            return 0.0
        
        return (n * sum_pv - sum_p * sum_v) / denominator
    
    def get_statistics(self) -> dict:
        """Return comprehensive statistics."""
        if not self.period_metrics:
            return {}
        
        stats = {
            "total_periods": len(self.period_metrics),
            "first_period": self.period_metrics[0].period,
            "last_period": self.period_metrics[-1].period,
        }
        
        # Add averages and trends for key metrics
        key_metrics = [
            "unemployment_rate",
            "avg_wage_human",
            "ai_employment_share",
            "gini_coefficient",
            "total_output",
        ]
        
        for metric in key_metrics:
            stats[f"{metric}_avg"] = self.calculate_average(metric)
            stats[f"{metric}_trend"] = self.calculate_trend(metric)
        
        return stats


class InequalityAnalyzer:
    """Analyzes income and employment inequality."""
    
    def __init__(self, metrics_tracker: MetricsTracker):
        self.tracker = metrics_tracker
    
    def get_inequality_evolution(self) -> Dict[str, List[Tuple[int, float]]]:
        """Get time series of inequality indices."""
        return {
            "gini": self.tracker.get_metric_series("gini_coefficient"),
            "theil": self.tracker.get_metric_series("theil_index"),
            "wage_gap": self.tracker.get_metric_series("wage_gap_ratio"),
        }
    
    def get_inequality_summary(self) -> dict:
        """Calculate inequality summary statistics."""
        if not self.tracker.period_metrics:
            return {}
        
        first_gini = self.tracker.period_metrics[0].gini_coefficient
        last_gini = self.tracker.period_metrics[-1].gini_coefficient
        
        first_wage_gap = self.tracker.period_metrics[0].wage_gap_ratio
        last_wage_gap = self.tracker.period_metrics[-1].wage_gap_ratio
        
        return {
            "gini_start": first_gini,
            "gini_end": last_gini,
            "gini_change": last_gini - first_gini,
            "wage_gap_start": first_wage_gap,
            "wage_gap_end": last_wage_gap,
            "wage_gap_increase": last_wage_gap - first_wage_gap,
            "avg_gini": self.tracker.calculate_average("gini_coefficient"),
            "gini_trend": self.tracker.calculate_trend("gini_coefficient"),
        }


class LaborMarketAnalyzer:
    """Analyzes labor market dynamics."""
    
    def __init__(self, metrics_tracker: MetricsTracker):
        self.tracker = metrics_tracker
    
    def get_unemployment_by_skill(self) -> Dict[str, List[Tuple[int, float]]]:
        """Get unemployment by skill level over time."""
        return {
            "low_skill": self.tracker.get_metric_series("low_skill_unemployment"),
            "high_skill": self.tracker.get_metric_series("high_skill_unemployment"),
        }
    
    def get_wage_by_skill(self) -> Dict[str, List[Tuple[int, float]]]:
        """Get wages by skill level over time."""
        return {
            "low_skill": self.tracker.get_metric_series("low_skill_avg_wage"),
            "high_skill": self.tracker.get_metric_series("high_skill_avg_wage"),
        }
    
    def get_match_efficiency(self) -> float:
        """Calculate average matching efficiency (match rate)."""
        avg = self.tracker.calculate_average("job_match_rate")
        return avg


class TechnologyAnalyzer:
    """Analyzes AI adoption and productivity."""
    
    def __init__(self, metrics_tracker: MetricsTracker):
        self.tracker = metrics_tracker
    
    def get_adoption_path(self) -> List[Tuple[int, float]]:
        """Get AI adoption rate over time."""
        return self.tracker.get_metric_series("ai_employment_share")
    
    def get_adoption_acceleration(self) -> float:
        """Calculate acceleration of adoption (2nd derivative)."""
        series = self.get_adoption_path()
        if len(series) < 3:
            return 0.0
        
        # Calculate discrete 2nd derivative
        periods = [p for p, _ in series]
        values = [v for _, v in series]
        
        # Δ²f ≈ f[i+1] - 2*f[i] + f[i-1]
        accel = sum(values[i+1] - 2*values[i] + values[i-1] 
                   for i in range(1, len(values)-1))
        
        return accel / (len(values) - 2) if len(values) > 2 else 0.0
    
    def get_productivity_growth(self) -> float:
        """Calculate average productivity growth (output per worker)."""
        return self.tracker.calculate_trend("output_per_worker")
    
    def get_r_and_d_intensity(self) -> float:
        """Get average R&D as share of output."""
        return self.tracker.calculate_average("r_and_d_as_share_of_output")


class PolicyAnalyzer:
    """Analyzes policy effectiveness."""
    
    def __init__(self, metrics_tracker: MetricsTracker):
        self.tracker = metrics_tracker
    
    def get_ui_metrics(self) -> dict:
        """Get UI program statistics."""
        if not self.tracker.period_metrics:
            return {}
        
        total_recipients = sum(m.ui_recipients for m in self.tracker.period_metrics)
        total_spending = sum(m.ui_spending for m in self.tracker.period_metrics)
        avg_spending = total_recipients / len(self.tracker.period_metrics) if self.tracker.period_metrics else 0
        
        return {
            "total_recipients": total_recipients,
            "total_spending": total_spending,
            "avg_recipients_per_period": total_recipients / len(self.tracker.period_metrics) if self.tracker.period_metrics else 0,
            "avg_spending_per_period": total_spending / len(self.tracker.period_metrics) if self.tracker.period_metrics else 0,
        }
    
    def get_retraining_metrics(self) -> dict:
        """Get retraining program statistics."""
        if not self.tracker.period_metrics:
            return {}
        
        total_graduates = sum(m.retraining_graduates for m in self.tracker.period_metrics)
        total_spending = sum(m.retraining_spending for m in self.tracker.period_metrics)
        
        return {
            "total_graduates": total_graduates,
            "total_spending": total_spending,
            "avg_graduates_per_period": total_graduates / len(self.tracker.period_metrics) if self.tracker.period_metrics else 0,
            "cost_per_graduate": total_spending / total_graduates if total_graduates > 0 else 0,
        }
    
    def get_policy_cost_benefit(self) -> dict:
        """Estimate policy cost-benefit."""
        ui_metrics = self.get_ui_metrics()
        retraining_metrics = self.get_retraining_metrics()
        
        total_cost = ui_metrics["total_spending"] + retraining_metrics["total_spending"]
        
        # Workers helped by policies
        helped_workers = ui_metrics["total_recipients"] + retraining_metrics["total_graduates"]
        
        return {
            "total_policy_cost": total_cost,
            "workers_helped": helped_workers,
            "cost_per_worker_helped": total_cost / helped_workers if helped_workers > 0 else 0,
        }


class ExportManager:
    """Manages data export to various formats."""
    
    @staticmethod
    def to_dict_list(metrics_tracker: MetricsTracker) -> List[dict]:
        """Convert metrics to list of dictionaries."""
        return [m.to_dict() for m in metrics_tracker.period_metrics]
    
    @staticmethod
    def to_dataframe(metrics_tracker: MetricsTracker):
        """Convert to pandas DataFrame (requires pandas installed)."""
        try:
            import pandas as pd
            return pd.DataFrame(ExportManager.to_dict_list(metrics_tracker))
        except ImportError:
            logger.warning("pandas not available for export")
            return None
    
    @staticmethod
    def to_csv(metrics_tracker: MetricsTracker, filepath: str):
        """Export metrics to CSV."""
        df = ExportManager.to_dataframe(metrics_tracker)
        if df is not None:
            df.to_csv(filepath, index=False)
            logger.info(f"Exported {len(df)} periods to {filepath}")
        else:
            logger.error("Could not export to CSV without pandas")
    
    @staticmethod
    def to_json(metrics_tracker: MetricsTracker) -> str:
        """Convert to JSON string."""
        try:
            import json
            return json.dumps(ExportManager.to_dict_list(metrics_tracker), indent=2)
        except ImportError:
            logger.error("json module not available")
            return ""
