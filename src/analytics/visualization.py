"""Visualization utilities."""

import logging
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional

logger = logging.getLogger(__name__)


def plot_time_series(
    df: pd.DataFrame,
    columns: list,
    title: str = "Simulation Results",
    figsize: tuple = (12, 6)
) -> None:
    """Create static matplotlib plot of time series.
    
    Args:
        df: Results DataFrame
        columns: List of column names to plot
        title: Plot title
        figsize: Figure size
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    for col in columns:
        if col in df.columns:
            ax.plot(df["period"], df[col], label=col)
    
    ax.set_xlabel("Period")
    ax.set_ylabel("Value")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return fig


def create_interactive_dashboard(df: pd.DataFrame):
    """Create interactive Plotly dashboard.
    
    Args:
        df: Results DataFrame
    """
    # TODO: Implement interactive dashboard
    pass


def export_results(df: pd.DataFrame, filepath: str) -> None:
    """Export results to CSV.
    
    Args:
        df: Results DataFrame
        filepath: Output filepath
    """
    df.to_csv(filepath, index=False)
    logger.info(f"Results exported to {filepath}")
