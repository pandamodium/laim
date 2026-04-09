"""
AI Labor Market Impact Analysis — Scenario Runner
===================================================
Runs 6 economic scenarios over a 20-year horizon (240 monthly periods)
to assess the potential impacts of AI on labor markets.

Scenarios:
1. No AI (counterfactual baseline)
2. Moderate AI adoption (current trajectory)
3. Aggressive AI (rapid, cheap, highly capable AI)
4. AI as Complement (low substitutability — AI augments humans)
5. Aggressive AI + Policy Response (retraining, subsidies)
6. Superstar Economy (high firm dispersion + aggressive AI)
"""

import logging
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

from src.simulation.engine import SimulationEngine
from src.config.parameters import SimulationConfig


# ── Scenario Definitions ──────────────────────────────────────────────────────

SCENARIOS = {
    "1_No_AI": {
        "description": "Counterfactual: no meaningful AI adoption",
        "params": dict(
            ai_productivity_multiplier=0.1,   # AI essentially useless
            ai_wage_ratio=2.0,                # and expensive
            ai_initial_adoption_share=0.0,
            simulation_periods=240,
            random_seed=42,
        ),
    },
    "2_Moderate_AI": {
        "description": "Current trajectory: moderate AI capability and gradual adoption",
        "params": dict(
            ai_productivity_multiplier=1.5,
            ai_wage_ratio=0.5,
            ai_initial_adoption_share=0.1,
            simulation_periods=240,
            random_seed=42,
        ),
    },
    "3_Aggressive_AI": {
        "description": "Rapid AI progress: highly capable and cheap AI",
        "params": dict(
            ai_productivity_multiplier=3.0,   # AI 3× as productive as humans
            ai_wage_ratio=0.25,               # and very cheap
            ai_initial_adoption_share=0.15,
            firm_substitution_elasticity=2.0, # easier to swap humans for AI
            simulation_periods=240,
            random_seed=42,
        ),
    },
    "4_AI_as_Complement": {
        "description": "AI augments humans: low substitutability, productivity boost",
        "params": dict(
            ai_productivity_multiplier=2.0,
            ai_wage_ratio=0.5,
            ai_initial_adoption_share=0.1,
            firm_substitution_elasticity=0.5, # complements, not substitutes
            simulation_periods=240,
            random_seed=42,
        ),
    },
    "5_Aggressive_AI_Policy": {
        "description": "Aggressive AI + active policy response (retraining + subsidies)",
        "params": dict(
            ai_productivity_multiplier=3.0,
            ai_wage_ratio=0.25,
            ai_initial_adoption_share=0.15,
            firm_substitution_elasticity=2.0,
            # Policy levers ON
            retraining_program_enabled=True,
            retraining_success_rate=0.7,
            retraining_productivity_boost=0.15,
            wage_subsidy_enabled=True,
            wage_subsidy_amount=500.0,
            r_and_d_tax_credit_enabled=True,
            r_and_d_tax_credit_rate=0.25,
            ui_replacement_rate=0.6,          # more generous UI
            simulation_periods=240,
            random_seed=42,
        ),
    },
    "6_Superstar_Economy": {
        "description": "Aggressive AI + high firm dispersion → winner-take-most",
        "params": dict(
            ai_productivity_multiplier=3.0,
            ai_wage_ratio=0.25,
            ai_initial_adoption_share=0.15,
            firm_substitution_elasticity=2.0,
            firm_productivity_dispersion=1.0, # much higher dispersion (default 0.5)
            num_firms=6,                      # more firms to see dispersion
            simulation_periods=240,
            random_seed=42,
        ),
    },
}


# ── Run All Scenarios ─────────────────────────────────────────────────────────

def run_scenario(name: str, spec: dict) -> pd.DataFrame:
    """Run a single scenario and return the results DataFrame."""
    print(f"\n{'='*60}")
    print(f"  Running: {name}")
    print(f"  {spec['description']}")
    print(f"{'='*60}")

    config = SimulationConfig(**spec["params"])
    engine = SimulationEngine(config)
    results = engine.run()
    results["scenario"] = name
    return results


def compute_summary(name: str, df: pd.DataFrame) -> dict:
    """Compute key summary statistics for a scenario run."""
    n = len(df)
    first_year = df.iloc[:12]        # months 1-12
    last_year = df.iloc[-12:]        # months 229-240
    mid = df.iloc[n//2 - 6 : n//2 + 6]  # around year 10

    avg_wage_start = first_year["avg_wage_human"].mean()
    avg_wage_end = last_year["avg_wage_human"].mean()
    wage_growth_total = (avg_wage_end / avg_wage_start - 1) * 100 if avg_wage_start > 0 else 0

    return {
        "scenario": name,
        # Unemployment
        "unemp_rate_yr1": first_year["unemployment_rate"].mean() * 100,
        "unemp_rate_yr10": mid["unemployment_rate"].mean() * 100,
        "unemp_rate_yr20": last_year["unemployment_rate"].mean() * 100,
        "peak_unemp": df["unemployment_rate"].max() * 100,
        # Wages
        "avg_wage_yr1": avg_wage_start,
        "avg_wage_yr20": avg_wage_end,
        "wage_change_pct": wage_growth_total,
        # Output
        "total_output_yr1": first_year["total_output"].mean(),
        "total_output_yr20": last_year["total_output"].mean(),
        "output_growth_pct": (
            (last_year["total_output"].mean() / max(0.01, first_year["total_output"].mean()) - 1) * 100
        ),
        # Employment composition
        "human_emp_yr1": first_year["num_employed_human"].mean(),
        "human_emp_yr20": last_year["num_employed_human"].mean(),
        "ai_emp_yr20": last_year["num_employed_ai"].mean(),
        "ai_share_yr20": (
            last_year["num_employed_ai"].mean()
            / max(1, last_year["num_employed_ai"].mean() + last_year["num_employed_human"].mean())
            * 100
        ),
        # Firm dynamics
        "firms_yr20": last_year["num_firms"].mean(),
        "total_firm_entries": df["new_firms_entered"].sum(),
        "total_firm_exits": df["firms_exited"].sum(),
        # Profit
        "avg_profit_yr1": first_year["total_profit"].mean(),
        "avg_profit_yr20": last_year["total_profit"].mean(),
    }


def print_comparison_table(summaries: list[dict]):
    """Print a formatted comparison table."""
    summary_df = pd.DataFrame(summaries)
    summary_df = summary_df.set_index("scenario")

    print("\n\n" + "=" * 100)
    print("  SCENARIO COMPARISON — AI LABOR MARKET IMPACT ANALYSIS")
    print("=" * 100)

    # Unemployment
    print("\n── UNEMPLOYMENT RATE (%) ─────────────────────────────────")
    cols = ["unemp_rate_yr1", "unemp_rate_yr10", "unemp_rate_yr20", "peak_unemp"]
    print(summary_df[cols].round(1).to_string())

    # Wages
    print("\n── WAGES ─────────────────────────────────────────────────")
    cols = ["avg_wage_yr1", "avg_wage_yr20", "wage_change_pct"]
    print(summary_df[cols].round(2).to_string())

    # Output
    print("\n── OUTPUT & PRODUCTIVITY ──────────────────────────────────")
    cols = ["total_output_yr1", "total_output_yr20", "output_growth_pct"]
    print(summary_df[cols].round(1).to_string())

    # Employment composition
    print("\n── EMPLOYMENT COMPOSITION ─────────────────────────────────")
    cols = ["human_emp_yr1", "human_emp_yr20", "ai_emp_yr20", "ai_share_yr20"]
    print(summary_df[cols].round(1).to_string())

    # Firm dynamics
    print("\n── FIRM DYNAMICS ──────────────────────────────────────────")
    cols = ["firms_yr20", "total_firm_entries", "total_firm_exits", "avg_profit_yr20"]
    print(summary_df[cols].round(1).to_string())

    return summary_df


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    output_dir = Path("outputs/scenario_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    summaries = []

    for name, spec in SCENARIOS.items():
        df = run_scenario(name, spec)
        all_results.append(df)
        summary = compute_summary(name, df)
        summaries.append(summary)

        # Save individual run
        df.to_csv(output_dir / f"{name}_results.csv", index=False)
        print(f"  ✓ {name}: unemployment yr20={summary['unemp_rate_yr20']:.1f}%, "
              f"wage Δ={summary['wage_change_pct']:+.1f}%, "
              f"AI share={summary['ai_share_yr20']:.1f}%")

    # Print master comparison
    summary_df = print_comparison_table(summaries)

    # Save combined outputs
    combined = pd.concat(all_results, ignore_index=True)
    combined.to_csv(output_dir / "all_scenarios_combined.csv", index=False)
    summary_df.to_csv(output_dir / "scenario_summary.csv")

    print(f"\n\nResults saved to {output_dir.resolve()}")
    print("Done.")
