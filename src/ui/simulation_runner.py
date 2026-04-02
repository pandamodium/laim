"""Streaming simulation runner for Streamlit.

Runs the simulation period-by-period, updating progress and live charts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict

from src.config.parameters import SimulationConfig
from src.simulation.engine import SimulationEngine

# How often to refresh the live charts (in periods)
CHART_REFRESH_INTERVAL = 12  # monthly sim → annual chart updates


def _build_live_figure(records: List[Dict]) -> go.Figure:
    """Build a 2x2 live preview figure from collected records."""
    df = pd.DataFrame(records)
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Unemployment Rate",
            "Average Human Wage",
            "AI Employment Share",
            "R&D Spending",
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    if "unemployment_rate" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["period"], y=df["unemployment_rate"],
                       mode="lines", line=dict(color="#e74c3c", width=2)),
            row=1, col=1,
        )
    if "avg_wage_human" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["period"], y=df["avg_wage_human"],
                       mode="lines", line=dict(color="#3498db", width=2)),
            row=1, col=2,
        )
    if "ai_employment_share" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["period"], y=df["ai_employment_share"],
                       mode="lines", line=dict(color="#9b59b6", width=2)),
            row=2, col=1,
        )
    if "total_r_and_d_spending" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["period"], y=df["total_r_and_d_spending"],
                       mode="lines", line=dict(color="#e67e22", width=2)),
            row=2, col=2,
        )

    fig.update_layout(
        height=420,
        showlegend=False,
        template="plotly_white",
        margin=dict(l=50, r=30, t=40, b=30),
    )
    fig.update_yaxes(title_text="Rate", row=1, col=1)
    fig.update_yaxes(title_text="Wage ($)", row=1, col=2)
    fig.update_yaxes(title_text="Share", row=2, col=1)
    fig.update_yaxes(title_text="Spending ($)", row=2, col=2)

    return fig


def run_simulation_streaming(config: SimulationConfig) -> pd.DataFrame:
    """Run simulation with live streaming progress and charts.

    Args:
        config: Validated SimulationConfig.

    Returns:
        DataFrame of per-period metrics.
    """
    total_periods = config.simulation_periods
    engine = SimulationEngine(config)
    records: List[Dict] = []

    # Streamlit containers for live updates
    progress_bar = st.progress(0, text="Initializing simulation...")
    status_text = st.empty()
    chart_placeholder = st.empty()

    for period in range(total_periods):
        # Check for early stop
        if st.session_state.get("stop_simulation", False):
            status_text.warning(f"Simulation stopped at period {period}.")
            break

        engine.step()
        stats = engine.get_aggregate_statistics()
        stats["period"] = period
        records.append(stats)

        # Update progress
        pct = (period + 1) / total_periods
        year = (period + 1) / 12
        progress_bar.progress(pct, text=f"Period {period + 1}/{total_periods} (Year {year:.1f})")

        # Refresh charts at interval
        if (period + 1) % CHART_REFRESH_INTERVAL == 0 or period == total_periods - 1:
            fig = _build_live_figure(records)
            chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"live_{period}")

    progress_bar.progress(1.0, text="Simulation complete!")
    status_text.success(
        f"✅ Completed {len(records)} periods ({len(records)/12:.1f} years)"
    )

    return pd.DataFrame(records)
