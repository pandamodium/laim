"""LAIM — AI Labor Market Simulation UI

Launch with:  streamlit run app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on the path so `src.*` imports resolve
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.config.parameters import SimulationConfig
from src.ui.parameter_panel import render_parameter_panel, build_config_from_state
from src.ui.simulation_runner import run_simulation_streaming
from src.ui.dashboard_view import render_dashboard
from src.ui.scenario_manager import (
    init_scenarios,
    save_scenario,
    get_scenario_names,
    render_scenario_comparison,
)
from src.ui.run_store import RunStore
from src.ui.export import render_export_controls

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="LAIM — AI Labor Market Simulation",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Tighten sidebar expander padding */
    section[data-testid="stSidebar"] .stExpander {
        margin-bottom: -0.5rem;
    }
    /* Metric cards */
    [data-testid="stMetric"] {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
init_scenarios()
if "metrics_df" not in st.session_state:
    st.session_state.metrics_df = None
if "config" not in st.session_state:
    st.session_state.config = None
if "run_name" not in st.session_state:
    st.session_state.run_name = "Baseline"
if "stop_simulation" not in st.session_state:
    st.session_state.stop_simulation = False

run_store = RunStore(base_dir=_project_root / "outputs" / "runs")

# ---------------------------------------------------------------------------
# Sidebar — parameter panel
# ---------------------------------------------------------------------------
params = render_parameter_panel()

# ---------------------------------------------------------------------------
# Main area — tabs
# ---------------------------------------------------------------------------
st.title("🏭 LAIM — AI Labor Market Simulation")

tab_run, tab_dash, tab_compare, tab_history = st.tabs(
    ["▶ Run", "📊 Dashboard", "📈 Compare", "🗂 History"]
)

# ======== RUN TAB ========
with tab_run:
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.session_state.run_name = st.text_input(
            "Run Name", value=st.session_state.run_name,
        )

    with col_right:
        st.write("")  # spacer
        st.write("")
        run_clicked = st.button("🚀 Run Simulation", type="primary", use_container_width=True)

    # Validation
    config_error = None
    try:
        config = build_config_from_state(params)
    except Exception as e:
        config_error = str(e)
        config = None

    if config_error:
        st.error(f"Invalid parameters: {config_error}")

    # Run simulation
    if run_clicked and config is not None:
        st.session_state.stop_simulation = False
        st.session_state.config = config

        metrics_df = run_simulation_streaming(config)
        st.session_state.metrics_df = metrics_df

        # Auto-save to disk
        run_store.save(st.session_state.run_name, metrics_df, config)

        # Offer to save as scenario for comparison
        st.divider()
        save_cols = st.columns([3, 1])
        with save_cols[0]:
            st.info("Save this run as a named scenario to compare with other runs.")
        with save_cols[1]:
            if st.button("💾 Save as Scenario"):
                save_scenario(
                    st.session_state.run_name,
                    metrics_df,
                    params,
                )
                st.success(f"Saved scenario: {st.session_state.run_name}")
    elif st.session_state.metrics_df is not None:
        # Show last run's save prompt
        st.caption(f"Last run: {st.session_state.run_name} ({len(st.session_state.metrics_df)} periods)")
        if st.button("💾 Save Last Run as Scenario"):
            save_scenario(
                st.session_state.run_name,
                st.session_state.metrics_df,
                params,
            )
            st.success(f"Saved scenario: {st.session_state.run_name}")

# ======== DASHBOARD TAB ========
with tab_dash:
    if st.session_state.metrics_df is not None:
        render_dashboard(st.session_state.metrics_df)
        st.divider()
        render_export_controls(
            st.session_state.metrics_df,
            st.session_state.config or SimulationConfig(),
            st.session_state.run_name,
        )
    else:
        st.info("Run a simulation to view the dashboard.")

# ======== COMPARE TAB ========
with tab_compare:
    render_scenario_comparison()

# ======== HISTORY TAB ========
with tab_history:
    st.header("🗂 Past Runs")
    runs = run_store.list_runs()

    if not runs:
        st.info("No saved runs yet. Run a simulation to get started.")
    else:
        for run_info in runs:
            with st.expander(
                f"**{run_info['name']}** — {run_info['created'][:16]} "
                f"({run_info['num_periods']} periods)"
            ):
                col_a, col_b, col_c = st.columns(3)
                path = run_info["path"]
                key_suffix = str(path)

                with col_a:
                    if st.button("📂 Load into Dashboard", key=f"load_{key_suffix}"):
                        metrics_df, loaded_config = run_store.load(path)
                        st.session_state.metrics_df = metrics_df
                        st.session_state.config = loaded_config
                        st.session_state.run_name = run_info["name"]
                        st.success(f"Loaded: {run_info['name']}")
                        st.rerun()

                with col_b:
                    if st.button("📈 Add to Comparison", key=f"compare_{key_suffix}"):
                        metrics_df, _ = run_store.load(path)
                        save_scenario(run_info["name"], metrics_df, {})
                        st.success(f"Added to comparison: {run_info['name']}")

                with col_c:
                    if st.button("🗑 Delete", key=f"del_{key_suffix}"):
                        run_store.delete(path)
                        st.success(f"Deleted: {run_info['name']}")
                        st.rerun()
