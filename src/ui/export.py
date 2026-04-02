"""Export utilities for HTML dashboard and CSV download.

Generates a single self-contained HTML file combining all dashboard
sections with tab navigation, plus CSV/JSON download helpers.
"""

import io
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

from src.analytics.dashboard import DashboardBuilder, DashboardConfig
from src.config.parameters import SimulationConfig


def _combined_html(metrics_df: pd.DataFrame, run_name: str) -> str:
    """Build a single self-contained HTML file with all dashboards.

    Uses Bootstrap tabs to wrap individual Plotly chart divs.
    """
    builder = DashboardBuilder(DashboardConfig())

    # Collect dashboard figures
    sections = [
        ("Overview", builder.create_overview_dashboard(metrics_df, save=False)),
        ("Labor Market", builder.create_labor_market_dashboard(metrics_df, save=False)),
        ("Technology", builder.create_technology_dashboard(metrics_df, save=False)),
        ("Firm Dynamics", builder.create_firm_dynamics_dashboard(metrics_df, save=False)),
        ("Inequality", builder.create_inequality_dashboard(metrics_df, save=False)),
    ]

    # Build tab nav + content
    tab_buttons = []
    tab_panes = []
    for i, (label, fig) in enumerate(sections):
        tab_id = label.lower().replace(" ", "_").replace("&", "and")
        active = "active" if i == 0 else ""
        selected = "true" if i == 0 else "false"
        show = "show active" if i == 0 else ""

        tab_buttons.append(
            f'<li class="nav-item"><button class="nav-link {active}" '
            f'data-bs-toggle="tab" data-bs-target="#tab_{tab_id}" type="button" '
            f'aria-selected="{selected}">{label}</button></li>'
        )

        chart_html = fig.to_html(full_html=False, include_plotlyjs=False)
        tab_panes.append(
            f'<div class="tab-pane fade {show}" id="tab_{tab_id}">{chart_html}</div>'
        )

    tabs_nav = "\n".join(tab_buttons)
    tabs_content = "\n".join(tab_panes)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAIM Dashboard — {run_name}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
      rel="stylesheet"
      integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YcnS/1CSXIV6Zg/A"
      crossorigin="anonymous">
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js" charset="utf-8"></script>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  .nav-tabs {{ margin-bottom: 1rem; }}
  .tab-content {{ padding: 0.5rem; }}
</style>
</head>
<body>
<div class="container-fluid py-3">
  <h2>LAIM Simulation Dashboard</h2>
  <p class="text-muted">{run_name} &mdash; Generated {timestamp}</p>
  <ul class="nav nav-tabs" role="tablist">
    {tabs_nav}
  </ul>
  <div class="tab-content">
    {tabs_content}
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
        crossorigin="anonymous"></script>
</body>
</html>"""
    return html


def export_combined_html(
    metrics_df: pd.DataFrame,
    run_name: str,
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate and save a combined dashboard HTML file.

    Args:
        metrics_df: Simulation results.
        run_name: Name for this run / filename base.
        output_dir: Where to write the file. Defaults to outputs/dashboards/.

    Returns:
        Path to the written file.
    """
    if output_dir is None:
        output_dir = Path("outputs/dashboards")
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in run_name)
    filename = f"combined_{safe_name}.html"
    path = output_dir / filename

    html = _combined_html(metrics_df, run_name)
    path.write_text(html, encoding="utf-8")
    return path


def export_csv(metrics_df: pd.DataFrame) -> bytes:
    """Return metrics DataFrame as CSV bytes for st.download_button."""
    return metrics_df.to_csv(index=False).encode("utf-8")


def export_config_json(config: SimulationConfig) -> bytes:
    """Return config as JSON bytes for st.download_button."""
    return config.model_dump_json(indent=2).encode("utf-8")


def render_export_controls(
    metrics_df: pd.DataFrame,
    config: SimulationConfig,
    run_name: str,
) -> None:
    """Render export buttons in the Streamlit UI.

    Args:
        metrics_df: Current simulation results.
        config: The config used for this run.
        run_name: Name for the run.
    """
    st.subheader("📥 Export")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Generate HTML Dashboard", type="primary"):
            path = export_combined_html(metrics_df, run_name)
            st.success(f"Saved to `{path}`")

    with col2:
        csv_data = export_csv(metrics_df)
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name=f"{run_name}_metrics.csv",
            mime="text/csv",
        )

    with col3:
        json_data = export_config_json(config)
        st.download_button(
            "Download Config JSON",
            data=json_data,
            file_name=f"{run_name}_config.json",
            mime="application/json",
        )
