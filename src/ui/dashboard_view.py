"""Dashboard view for rendering simulation results in Streamlit.

Displays summary metric cards and all interactive Plotly dashboards.
"""

import streamlit as st
import pandas as pd

from src.analytics.dashboard import DashboardBuilder, DashboardConfig


def _render_summary_metrics(df: pd.DataFrame) -> None:
    """Render key summary metrics as st.metric cards."""
    cols = st.columns(5)

    if "unemployment_rate" in df.columns:
        unemp = df["unemployment_rate"]
        cols[0].metric(
            "Unemployment Rate",
            f"{unemp.iloc[-1]:.2%}",
            delta=f"{unemp.iloc[-1] - unemp.iloc[0]:.2%}",
            delta_color="inverse",
        )

    if "avg_wage_human" in df.columns:
        wage = df["avg_wage_human"]
        growth = (wage.iloc[-1] / max(wage.iloc[0], 0.001) - 1) * 100
        cols[1].metric(
            "Avg Human Wage",
            f"${wage.iloc[-1]:,.2f}",
            delta=f"{growth:+.1f}%",
        )

    if "ai_employment_share" in df.columns:
        ai = df["ai_employment_share"]
        cols[2].metric(
            "AI Employment Share",
            f"{ai.iloc[-1]:.2%}",
            delta=f"{ai.iloc[-1] - ai.iloc[0]:.2%}",
            delta_color="off",
        )

    if "total_r_and_d_spending" in df.columns:
        rd = df["total_r_and_d_spending"]
        cols[3].metric(
            "Total R&D Spending",
            f"${rd.sum():,.0f}",
            delta=f"${rd.mean():,.0f}/period",
            delta_color="off",
        )

    if "num_firms" in df.columns:
        firms = df["num_firms"]
        cols[4].metric(
            "Firms",
            f"{firms.iloc[-1]:.0f}",
            delta=f"{firms.iloc[-1] - firms.iloc[0]:+.0f}",
        )


def render_dashboard(metrics_df: pd.DataFrame) -> None:
    """Render the full combined dashboard page.

    Args:
        metrics_df: DataFrame of per-period simulation metrics.
    """
    if metrics_df is None or metrics_df.empty:
        st.info("Run a simulation first to see results here.")
        return

    st.header("📊 Simulation Dashboard")

    # Summary cards
    _render_summary_metrics(metrics_df)
    st.divider()

    # Build dashboards without saving to disk
    builder = DashboardBuilder(DashboardConfig())

    # Overview
    st.subheader("Overview")
    fig = builder.create_overview_dashboard(metrics_df, save=False)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Labor Market
    st.subheader("Labor Market")
    fig = builder.create_labor_market_dashboard(metrics_df, save=False)
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

    # Technology & R&D
    st.subheader("Technology & R&D")
    fig = builder.create_technology_dashboard(metrics_df, save=False)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Firm Dynamics
    if "num_firms" in metrics_df.columns:
        st.subheader("Firm Dynamics")
        fig = builder.create_firm_dynamics_dashboard(metrics_df, save=False)
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    # Profitability & Revenue
    if "total_profit" in metrics_df.columns:
        st.subheader("Profitability & Revenue")
        fig = builder.create_profitability_dashboard(metrics_df, save=False)
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    # Inequality
    has_ineq = any(
        c in metrics_df.columns
        for c in ["gini_coefficient", "theil_index", "wage_gap_ratio"]
    )
    if has_ineq:
        st.subheader("Inequality & Distribution")
        fig = builder.create_inequality_dashboard(metrics_df, save=False)
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

    # Detailed period data
    with st.expander("📋 Raw Metrics Data", expanded=False):
        st.dataframe(metrics_df, use_container_width=True, height=300)
