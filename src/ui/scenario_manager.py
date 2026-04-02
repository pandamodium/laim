"""Scenario manager for comparing multiple simulation runs.

Stores named scenarios in session state and renders comparison dashboards.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List

from src.analytics.dashboard import DashboardBuilder, DashboardConfig

# Key metrics to compare across scenarios
COMPARISON_METRICS = [
    ("unemployment_rate", "Unemployment Rate"),
    ("avg_wage_human", "Average Human Wage ($)"),
    ("ai_employment_share", "AI Employment Share"),
    ("total_r_and_d_spending", "R&D Spending ($)"),
    ("num_firms", "Number of Firms"),
    ("total_output", "Total Output"),
]

MAX_SCENARIOS = 6


def init_scenarios() -> None:
    """Initialize scenario storage in session state."""
    if "scenarios" not in st.session_state:
        st.session_state.scenarios = {}


def save_scenario(name: str, metrics_df: pd.DataFrame, config_dict: dict) -> None:
    """Save a completed run as a named scenario.

    Args:
        name: Scenario display name.
        metrics_df: Simulation results DataFrame.
        config_dict: Configuration dict used for this run.
    """
    init_scenarios()
    if len(st.session_state.scenarios) >= MAX_SCENARIOS:
        st.warning(f"Maximum {MAX_SCENARIOS} scenarios. Remove one before adding another.")
        return
    st.session_state.scenarios[name] = {
        "metrics": metrics_df,
        "config": config_dict,
    }


def remove_scenario(name: str) -> None:
    """Remove a scenario by name."""
    st.session_state.scenarios.pop(name, None)


def get_scenario_names() -> List[str]:
    """Return list of saved scenario names."""
    init_scenarios()
    return list(st.session_state.scenarios.keys())


def _build_comparison_table(scenarios: Dict[str, dict]) -> pd.DataFrame:
    """Build a summary comparison table across scenarios."""
    rows = []
    for name, data in scenarios.items():
        df = data["metrics"]
        row = {"Scenario": name, "Periods": len(df)}
        if "unemployment_rate" in df.columns:
            row["Unemp (Final)"] = f"{df['unemployment_rate'].iloc[-1]:.2%}"
            row["Unemp (Mean)"] = f"{df['unemployment_rate'].mean():.2%}"
        if "avg_wage_human" in df.columns:
            w = df["avg_wage_human"]
            row["Wage (Final)"] = f"${w.iloc[-1]:,.2f}"
            row["Wage Growth"] = f"{(w.iloc[-1]/max(w.iloc[0],0.001)-1)*100:+.1f}%"
        if "ai_employment_share" in df.columns:
            row["AI Share (Final)"] = f"{df['ai_employment_share'].iloc[-1]:.2%}"
        if "num_firms" in df.columns:
            row["Firms (Final)"] = f"{df['num_firms'].iloc[-1]:.0f}"
        rows.append(row)
    return pd.DataFrame(rows)


def render_scenario_comparison() -> None:
    """Render the scenario comparison tab."""
    init_scenarios()
    scenarios = st.session_state.scenarios

    st.header("📈 Scenario Comparison")

    if len(scenarios) < 2:
        st.info(
            "Run at least 2 simulations and save them as scenarios to compare. "
            "Use the **Run** tab to execute simulations."
        )
        if scenarios:
            st.caption(f"Currently saved: {', '.join(scenarios.keys())}")
        return

    # Scenario management
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"Comparing {len(scenarios)} scenarios: {', '.join(scenarios.keys())}")
    with col2:
        to_remove = st.selectbox("Remove scenario", [""] + list(scenarios.keys()), key="sc_remove")
        if to_remove:
            remove_scenario(to_remove)
            st.rerun()

    # Summary table
    st.subheader("Summary Comparison")
    table = _build_comparison_table(scenarios)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.divider()

    # Overlay charts for each key metric
    builder = DashboardBuilder(DashboardConfig())
    scenario_dfs = {name: data["metrics"] for name, data in scenarios.items()}

    for metric_col, metric_label in COMPARISON_METRICS:
        # Skip if no scenario has this metric
        if not any(metric_col in df.columns for df in scenario_dfs.values()):
            continue

        fig = builder.create_scenario_comparison_dashboard(
            scenario_dfs, metric_col, metric_label, save=False,
        )
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)
