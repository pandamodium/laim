"""Metrics collection and data storage."""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from src.config import SimulationConfig

logger = logging.getLogger(__name__)


@dataclass
class PeriodMetrics:
    """Metrics recorded each period."""
    period: int
    num_firms: int
    num_employed_human: int
    num_employed_ai: int
    num_unemployed: int
    unemployment_rate: float
    avg_wage_human: float
    total_output: float
    total_profit: float
    job_vacancies: int
    job_matches: int
    new_firms_entered: int
    firms_exited: int
    avg_firm_size: float


class MetricsCollector:
    """Collects and stores metrics throughout simulation."""
    
    def __init__(self, config: SimulationConfig):
        """Initialize metrics collector.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        self.metrics_history: List[PeriodMetrics] = []
    
    def record_period(self, metrics: PeriodMetrics) -> None:
        """Record metrics for a period.
        
        Args:
            metrics: PeriodMetrics instance
        """
        self.metrics_history.append(metrics)
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """Get all metrics as DataFrame.
        
        Returns:
            DataFrame with all recorded metrics
        """
        if not self.metrics_history:
            logger.warning("No metrics recorded")
            return pd.DataFrame()
        
        data = [asdict(m) for m in self.metrics_history]
        return pd.DataFrame(data)
    
    def get_summary_statistics(self) -> Dict:
        """Compute summary statistics over full simulation.
        
        Returns:
            Dictionary of summary statistics
        """
        if not self.metrics_history:
            return {}
        
        df = self.get_results_dataframe()
        
        return {
            "avg_unemployment_rate": df["unemployment_rate"].mean(),
            "final_unemployment_rate": df["unemployment_rate"].iloc[-1],
            "avg_wage_human": df["avg_wage_human"].mean(),
            "final_wage_human": df["avg_wage_human"].iloc[-1],
            "total_output": df["total_output"].sum(),
            "avg_firm_count": df["num_firms"].mean(),
            "total_new_firms": df["new_firms_entered"].sum(),
            "total_firm_exits": df["firms_exited"].sum(),
        }
