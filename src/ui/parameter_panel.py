"""Parameter panel for the Streamlit sidebar.

Renders grouped parameter controls with preset scenario support.
"""

import streamlit as st
from typing import Dict, Any

from src.config.parameters import SimulationConfig, DEFAULT_CONFIG
from src.simulation.benchmarks import BenchmarkRunner, BenchmarkScenario


# Map preset names to BenchmarkScenario class variables
PRESETS: Dict[str, BenchmarkScenario] = {
    "Baseline": BenchmarkRunner.BASELINE,
    "High AI": BenchmarkRunner.HIGH_AI,
    "No AI": BenchmarkRunner.NO_AI,
    "Sectoral Shift": BenchmarkRunner.SECTORAL_SHIFT,
    "Policy + High AI": BenchmarkRunner.POLICY_PLUS_AI,
    "Custom": None,
}


def _get_preset_config(preset_name: str) -> SimulationConfig:
    """Get the SimulationConfig for a preset scenario."""
    scenario = PRESETS.get(preset_name)
    if scenario is None:
        return DEFAULT_CONFIG.model_copy()
    return scenario.get_config(DEFAULT_CONFIG)


def render_parameter_panel() -> Dict[str, Any]:
    """Render the sidebar parameter panel and return parameter values.

    Returns:
        Dictionary of parameter name -> value for all config fields.
    """
    st.sidebar.title("⚙️ Parameters")

    # --- Preset selector ---
    preset = st.sidebar.selectbox(
        "Scenario Preset",
        list(PRESETS.keys()),
        index=0,
        help="Select a preset to populate parameters, then fine-tune below.",
    )

    cfg = _get_preset_config(preset)
    params: Dict[str, Any] = {}

    # --- Simulation ---
    with st.sidebar.expander("🕐 Simulation", expanded=False):
        params["simulation_periods"] = st.slider(
            "Periods", 12, 1200, cfg.simulation_periods, step=12,
            help="Total periods (12/yr). 240 = 20 years.",
        )
        params["random_seed"] = st.number_input(
            "Random Seed", value=cfg.random_seed, step=1,
        )

    # --- Firms ---
    with st.sidebar.expander("🏢 Firms", expanded=False):
        params["num_firms"] = st.slider(
            "Number of Firms", 1, 20, cfg.num_firms,
        )
        params["firm_substitution_elasticity"] = st.slider(
            "CES Substitution Elasticity", 0.1, 10.0, cfg.firm_substitution_elasticity, step=0.1,
            help=">1 means human & AI are substitutes.",
        )
        params["output_demand_elasticity"] = st.slider(
            "Output Demand Elasticity", 0.1, 5.0, cfg.output_demand_elasticity, step=0.1,
        )

    # --- Human Labor ---
    with st.sidebar.expander("👷 Human Labor", expanded=False):
        params["initial_human_workers"] = st.number_input(
            "Initial Workers", min_value=100, max_value=1_000_000,
            value=cfg.initial_human_workers, step=100,
        )
        params["human_population_growth_rate"] = st.slider(
            "Population Growth Rate", 0.0, 0.10, cfg.human_population_growth_rate,
            step=0.005, format="%.3f",
        )
        params["separation_rate_employed"] = st.slider(
            "Job Separation Rate", 0.0, 0.20, cfg.separation_rate_employed,
            step=0.005, format="%.3f",
        )

    # --- AI ---
    with st.sidebar.expander("🤖 AI", expanded=True):
        params["ai_productivity_multiplier"] = st.slider(
            "AI Productivity Multiplier", 0.1, 10.0,
            cfg.ai_productivity_multiplier, step=0.1,
            help="AI output relative to human labor.",
        )
        params["ai_wage_ratio"] = st.slider(
            "AI Cost / Human Wage", 0.0, 2.0, cfg.ai_wage_ratio,
            step=0.05, format="%.2f",
        )
        params["ai_initial_adoption_share"] = st.slider(
            "Initial AI Adoption Share", 0.0, 1.0,
            cfg.ai_initial_adoption_share, step=0.05,
        )

    # --- Entrepreneurship ---
    with st.sidebar.expander("🚀 Entrepreneurship", expanded=False):
        params["base_entrepreneurship_rate"] = st.slider(
            "Base Rate", 0.0, 0.30, cfg.base_entrepreneurship_rate,
            step=0.01, format="%.2f",
        )
        params["entrepreneurship_unemployed_premium"] = st.slider(
            "Unemployed Premium", 1.0, 10.0,
            cfg.entrepreneurship_unemployed_premium, step=0.5,
        )
        params["min_capital_to_start_firm"] = st.number_input(
            "Min Capital to Start", min_value=0.0,
            value=cfg.min_capital_to_start_firm, step=10.0,
        )
        params["new_firm_initial_size"] = st.slider(
            "New Firm Initial Size", 1, 50, cfg.new_firm_initial_size,
        )

    # --- R&D ---
    with st.sidebar.expander("🔬 R&D", expanded=False):
        params["r_and_d_profit_share"] = st.slider(
            "R&D Profit Share", 0.0, 0.50,
            cfg.r_and_d_profit_share, step=0.01, format="%.2f",
        )
        params["r_and_d_efficiency"] = st.slider(
            "R&D Efficiency", 0.0, 0.20, cfg.r_and_d_efficiency,
            step=0.005, format="%.3f",
        )
        params["r_and_d_lag_periods"] = st.slider(
            "R&D Lag (periods)", 0, 12, cfg.r_and_d_lag_periods,
        )
        params["r_and_d_private_share"] = st.slider(
            "Private Benefit Share", 0.0, 1.0,
            cfg.r_and_d_private_share, step=0.1,
        )

    # --- Market Matching ---
    with st.sidebar.expander("🔗 Market Matching", expanded=False):
        params["matching_efficiency"] = st.slider(
            "Matching Efficiency", 0.1, 10.0,
            cfg.matching_efficiency, step=0.1,
        )
        params["matching_elasticity"] = st.slider(
            "Matching Elasticity", 0.0, 1.0,
            cfg.matching_elasticity, step=0.05,
        )

    # --- Wages & UI ---
    with st.sidebar.expander("💰 Wages & UI", expanded=False):
        params["ui_replacement_rate"] = st.slider(
            "UI Replacement Rate", 0.0, 1.0,
            cfg.ui_replacement_rate, step=0.05,
        )
        params["ui_benefit_duration_periods"] = st.slider(
            "UI Duration (periods)", 1, 104,
            cfg.ui_benefit_duration_periods,
        )
        params["reservation_wage_multiplier"] = st.slider(
            "Reservation Wage Multiplier", 0.0, 1.0,
            cfg.reservation_wage_multiplier, step=0.05,
        )
        params["wage_adjustment_speed"] = st.slider(
            "Wage Adjustment Speed", 0.0, 1.0,
            cfg.wage_adjustment_speed, step=0.05,
        )

    # --- Policy: Retraining ---
    with st.sidebar.expander("📚 Policy: Retraining", expanded=False):
        params["retraining_program_enabled"] = st.toggle(
            "Enable Retraining", value=cfg.retraining_program_enabled,
        )
        if params["retraining_program_enabled"]:
            params["retraining_cost"] = st.number_input(
                "Retraining Cost ($)", min_value=0.0,
                value=cfg.retraining_cost, step=500.0,
            )
            params["retraining_duration_periods"] = st.slider(
                "Duration (periods)", 1, 52,
                cfg.retraining_duration_periods,
            )
            params["retraining_success_rate"] = st.slider(
                "Success Rate", 0.0, 1.0,
                cfg.retraining_success_rate, step=0.05,
            )
            params["retraining_productivity_boost"] = st.slider(
                "Productivity Boost", 0.0, 1.0,
                cfg.retraining_productivity_boost, step=0.05,
            )
        else:
            params["retraining_cost"] = cfg.retraining_cost
            params["retraining_duration_periods"] = cfg.retraining_duration_periods
            params["retraining_success_rate"] = cfg.retraining_success_rate
            params["retraining_productivity_boost"] = cfg.retraining_productivity_boost

    # --- Policy: Subsidies & Credits ---
    with st.sidebar.expander("💳 Policy: Subsidies & Credits", expanded=False):
        params["wage_subsidy_enabled"] = st.toggle(
            "Enable Wage Subsidy", value=cfg.wage_subsidy_enabled,
        )
        if params["wage_subsidy_enabled"]:
            params["wage_subsidy_amount"] = st.number_input(
                "Subsidy Amount ($/qtr)", min_value=0.0,
                value=cfg.wage_subsidy_amount, step=100.0,
            )
            params["wage_subsidy_target_group"] = st.selectbox(
                "Target Group",
                ["displaced", "low_skill", "all"],
                index=["displaced", "low_skill", "all"].index(cfg.wage_subsidy_target_group),
            )
        else:
            params["wage_subsidy_amount"] = cfg.wage_subsidy_amount
            params["wage_subsidy_target_group"] = cfg.wage_subsidy_target_group

        params["r_and_d_tax_credit_enabled"] = st.toggle(
            "Enable R&D Tax Credit", value=cfg.r_and_d_tax_credit_enabled,
        )
        if params["r_and_d_tax_credit_enabled"]:
            params["r_and_d_tax_credit_rate"] = st.slider(
                "Tax Credit Rate", 0.0, 1.0,
                cfg.r_and_d_tax_credit_rate, step=0.05,
            )
        else:
            params["r_and_d_tax_credit_rate"] = cfg.r_and_d_tax_credit_rate

        params["hiring_tax_credit_enabled"] = st.toggle(
            "Enable Hiring Tax Credit", value=cfg.hiring_tax_credit_enabled,
        )
        if params["hiring_tax_credit_enabled"]:
            params["hiring_tax_credit_amount"] = st.number_input(
                "Credit per Hire ($)", min_value=0.0,
                value=cfg.hiring_tax_credit_amount, step=500.0,
            )
        else:
            params["hiring_tax_credit_amount"] = cfg.hiring_tax_credit_amount

    # --- Skills & Job Categories ---
    with st.sidebar.expander("🎯 Skills & Job Categories", expanded=False):
        params["use_skill_heterogeneity"] = st.toggle(
            "Skill Heterogeneity", value=cfg.use_skill_heterogeneity,
        )
        if params["use_skill_heterogeneity"]:
            params["skill_distribution_low_share"] = st.slider(
                "Low-Skill Share", 0.0, 1.0,
                cfg.skill_distribution_low_share, step=0.05,
            )
        else:
            params["skill_distribution_low_share"] = cfg.skill_distribution_low_share

        params["use_job_categories"] = st.toggle(
            "Job Categories", value=cfg.use_job_categories,
        )
        if params["use_job_categories"]:
            params["routine_job_share"] = st.slider(
                "Routine Share", 0.0, 1.0,
                cfg.routine_job_share, step=0.05,
            )
            params["management_job_share"] = st.slider(
                "Management Share", 0.0, 1.0,
                cfg.management_job_share, step=0.05,
            )
            # Creative share = 1 - routine - management
            creative = max(0.0, 1.0 - params["routine_job_share"] - params["management_job_share"])
            st.caption(f"Creative share: {creative:.0%}")
        else:
            params["routine_job_share"] = cfg.routine_job_share
            params["management_job_share"] = cfg.management_job_share

        params["job_category_ai_multipliers"] = cfg.job_category_ai_multipliers

    # --- AI Cost Curve ---
    with st.sidebar.expander("📉 AI Cost Curve", expanded=False):
        params["ai_cost_curve_learning_enabled"] = st.toggle(
            "Learning-by-Doing", value=cfg.ai_cost_curve_learning_enabled,
        )
        if params["ai_cost_curve_learning_enabled"]:
            params["ai_cost_learning_parameter"] = st.slider(
                "Learning Parameter (λ)", 0.0, 1.0,
                cfg.ai_cost_learning_parameter, step=0.05,
            )
            params["r_and_d_ai_cost_rate"] = st.number_input(
                "R&D Cost Reduction Rate", min_value=0.0,
                value=cfg.r_and_d_ai_cost_rate, step=0.001, format="%.4f",
            )
        else:
            params["ai_cost_learning_parameter"] = cfg.ai_cost_learning_parameter
            params["r_and_d_ai_cost_rate"] = cfg.r_and_d_ai_cost_rate

    # --- Advanced ---
    with st.sidebar.expander("🔧 Advanced", expanded=False):
        params["loss_periods_to_exit"] = st.slider(
            "Firm Exit After N Loss Periods", 1, 12,
            cfg.loss_periods_to_exit,
        )
        params["output_market_capacity"] = st.number_input(
            "Market Capacity (0=auto)", min_value=0.0,
            value=cfg.output_market_capacity, step=100.0,
        )
        params["output_price_intercept"] = st.slider(
            "Price Intercept", 0.1, 10.0,
            cfg.output_price_intercept, step=0.1,
        )
        params["use_worker_heterogeneity"] = st.toggle(
            "Worker Heterogeneity", value=cfg.use_worker_heterogeneity,
        )
        params["use_firm_learning"] = st.toggle(
            "Firm Learning", value=cfg.use_firm_learning,
        )
        params["use_wage_bargaining"] = st.toggle(
            "Wage Bargaining", value=cfg.use_wage_bargaining,
        )

    # Non-UI params (carry through defaults)
    params["output_log_frequency"] = cfg.output_log_frequency
    params["save_full_agent_history"] = cfg.save_full_agent_history

    return params


def build_config_from_state(params: Dict[str, Any]) -> SimulationConfig:
    """Create a validated SimulationConfig from UI parameter values.

    Args:
        params: Dictionary of parameter name -> value from render_parameter_panel.

    Returns:
        Validated SimulationConfig instance.

    Raises:
        pydantic.ValidationError: If parameter combination is invalid.
    """
    return SimulationConfig(**params)
