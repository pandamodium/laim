"""
Simulation Configuration and Parameters

All configurable parameters for the AI labor market simulation are centralized here.
Use Pydantic for validation and type checking.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SimulationConfig(BaseModel):
    """Main configuration object for simulation."""
    
    # ========== Firm Parameters ==========
    num_firms: int = Field(
        default=3, 
        ge=1, 
        le=20,
        description="Number of oligopolistic firms"
    )
    firm_substitution_elasticity: float = Field(
        default=1.5,
        ge=0.1,
        le=10,
        description="CES elasticity between human and AI labor (>1 means substitutes)"
    )
    firm_productivity_dispersion: float = Field(
        default=0.5,
        ge=0.0,
        le=2.0,
        description="Log-normal sigma for firm productivity draws. Higher = more superstar firms. 0 = identical firms."
    )
    labor_share_of_mpl: float = Field(
        default=0.65,
        ge=0.1,
        le=0.95,
        description="Fraction of marginal product of labor offered as wage (firms keep 1 - this as markup)"
    )
    output_demand_elasticity: float = Field(
        default=1.0,
        description="Price elasticity of output demand (for Cournot competition)"
    )
    
    # ========== Human Labor Supply ==========
    initial_human_workers: int = Field(
        default=1000,
        ge=100,
        le=1000000,
        description="Initial number of human workers in economy"
    )
    human_population_growth_rate: float = Field(
        default=0.02,
        ge=0,
        le=0.1,
        description="Annual growth rate of human population (enters labor supply)"
    )
    human_productivity_growth_rate: float = Field(
        default=0.015,
        ge=0,
        le=0.1,
        description="Annual baseline growth rate of human productivity (education, experience, tools). AI augmentation provides additional boost."
    )
    ai_augmentation_factor: float = Field(
        default=0.3,
        ge=0,
        le=1.0,
        description="How much AI coworkers boost human productivity. At AI_share=50%, human productivity grows an extra augmentation_factor * AI_share per year. Reflects humans using AI tools to be more effective."
    )
    separation_rate_employed: float = Field(
        default=0.02,
        ge=0,
        le=1,
        description="Monthly exogenous job separation rate (workers become unemployed)"
    )
    on_the_job_search_rate: float = Field(
        default=0.05,
        ge=0,
        le=1,
        description="Monthly probability an employed worker samples an outside offer (poaching)"
    )
    poaching_wage_threshold: float = Field(
        default=0.05,
        ge=0,
        le=1,
        description="Minimum wage premium (fraction) for a worker to switch firms"
    )
    
    # ========== AI Parameters ==========
    ai_productivity_multiplier: float = Field(
        default=1.5,
        ge=0.1,
        le=10,
        description="Relative productivity of AI vs human (AI units = multiplier × human units)"
    )
    ai_wage_ratio: float = Field(
        default=0.5,
        ge=0,
        le=5,
        description="AI cost-per-unit as ratio of human wage (captures hardware + electricity)"
    )
    ai_initial_adoption_share: float = Field(
        default=0.1,
        ge=0,
        le=1,
        description="Initial AI employment share (as fraction of total workforce)"
    )
    ai_adoption_speed: float = Field(
        default=0.05,
        ge=0.01,
        le=1.0,
        description="Maximum fraction of desired AI expansion a firm can achieve per period. Reflects implementation friction (integration, training, infrastructure). 0.05 = firms can add at most 5% of desired AI increase per month."
    )
    
    # ========== Entrepreneurship Parameters ==========
    base_entrepreneurship_rate: float = Field(
        default=0.05,
        ge=0,
        le=1,
        description="Base annual probability of forming new business"
    )
    entrepreneurship_unemployed_premium: float = Field(
        default=2.0,
        ge=1,
        le=10,
        description="Multiplier on entrepreneurship rate for unemployed (vs employed)"
    )
    min_capital_to_start_firm: float = Field(
        default=6.0,
        ge=0,
        description="Minimum accumulated savings needed to start business (~6 months of wages)"
    )
    new_firm_initial_size: int = Field(
        default=2,
        ge=1,
        le=50,
        description="Initial number of workers (on average) for new firm"
    )
    
    # ========== R&D Parameters ==========
    r_and_d_profit_share: float = Field(
        default=0.05,
        ge=0,
        le=0.5,
        description="Share of profits allocated to R&D spending"
    )
    r_and_d_efficiency: float = Field(
        default=0.01,
        ge=0,
        le=1,
        description="Productivity of R&D (% cost reduction per unit R&D spending)"
    )
    r_and_d_lag_periods: int = Field(
        default=2,
        ge=0,
        le=12,
        description="Number of periods for R&D to commercialize (lag)"
    )
    r_and_d_private_share: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Share of R&D benefit private to firm (rest spillover to others)"
    )
    
    # ========== Market Matching Parameters ==========
    matching_efficiency: float = Field(
        default=1.0,
        ge=0.1,
        le=10,
        description="Efficiency of matching function (higher = more matches)"
    )
    matching_elasticity: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Elasticity in matching function (unemployment vs vacancies)"
    )
    
    # ========== Wage and Labor Market Parameters ==========
    # ========== UI & Benefits Parameters ==========
    ui_replacement_rate: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Unemployment insurance as fraction of previous wage"
    )
    ui_benefit_duration_periods: int = Field(
        default=26,
        ge=1,
        le=260,
        description="Number of periods UI benefits last (26 = 6 months at monthly frequency)"
    )
    reservation_wage_multiplier: float = Field(
        default=0.8,
        ge=0,
        le=1,
        description="Reservation wage as fraction of UI benefits (if unemployed) or current wage (if searching)"
    )
    wage_adjustment_speed: float = Field(
        default=0.1,
        ge=0,
        le=1,
        description="Speed of wage adjustment toward equilibrium (Phillips curve)"
    )
    downward_wage_rigidity: float = Field(
        default=0.3,
        ge=0,
        le=1,
        description="Downward wage rigidity factor (0=fully rigid downward, 1=fully flexible). Wages fall at this fraction of the speed they rise."
    )
    
    # ========== Retraining Program Parameters ==========
    retraining_program_enabled: bool = Field(
        default=False,
        description="Enable worker retraining programs"
    )
    retraining_cost: float = Field(
        default=5000.0,
        ge=0,
        description="Cost to enroll unemployed worker in retraining"
    )
    retraining_duration_periods: int = Field(
        default=8,
        ge=1,
        le=52,
        description="Duration of retraining program (8 = 2 months)"
    )
    retraining_success_rate: float = Field(
        default=0.7,
        ge=0,
        le=1,
        description="Fraction of trainees successfully trained"
    )
    retraining_productivity_boost: float = Field(
        default=0.15,
        ge=0,
        le=1,
        description="Wage increase after successful retraining (15% boost)"
    )
    
    # ========== Wage Subsidy Parameters ==========
    wage_subsidy_enabled: bool = Field(
        default=False,
        description="Enable wage subsidies for hiring"
    )
    wage_subsidy_amount: float = Field(
        default=500.0,
        ge=0,
        description="Subsidy per worker per quarter"
    )
    wage_subsidy_target_group: str = Field(
        default="displaced",
        description="Target group for subsidy: 'displaced', 'low_skill', 'all'"
    )
    
    # ========== R&D Tax Credit Parameters ==========
    r_and_d_tax_credit_enabled: bool = Field(
        default=False,
        description="Enable R&D tax credits"
    )
    r_and_d_tax_credit_rate: float = Field(
        default=0.25,
        ge=0,
        le=1,
        description="R&D tax credit as fraction of R&D spending"
    )
    hiring_tax_credit_enabled: bool = Field(
        default=False,
        description="Enable tax credits for net job creation"
    )
    hiring_tax_credit_amount: float = Field(
        default=2000.0,
        ge=0,
        description="Tax credit per new hire in first 12 months"
    )
    
    # ========== Skill-Based Technical Change Parameters ==========
    use_skill_heterogeneity: bool = Field(
        default=False,
        description="Enable worker skill levels (low-skill vs high-skill)"
    )
    skill_distribution_low_share: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Fraction of workforce that are low-skill"
    )
    
    # ========== Job Category Parameters ==========
    use_job_categories: bool = Field(
        default=False,
        description="Enable job category classification (routine, management, creative)"
    )
    job_category_ai_multipliers: dict = Field(
        default={
            "routine": 2.0,
            "management": 0.5,
            "creative": 0.1
        },
        description="AI productivity multiplier by job category"
    )
    routine_job_share: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Fraction of jobs classified as routine"
    )
    management_job_share: float = Field(
        default=0.25,
        ge=0,
        le=1,
        description="Fraction of jobs classified as management"
    )
    
    # ========== AI Cost Curve Parameters ==========
    ai_cost_curve_learning_enabled: bool = Field(
        default=False,
        description="Enable learning-by-doing AI cost reductions"
    )
    ai_cost_learning_parameter: float = Field(
        default=0.3,
        ge=0,
        le=1,
        description="Learning parameter λ in cost curve: cost = base × (1 + adoption)^(-λ)"
    )
    r_and_d_ai_cost_rate: float = Field(
        default=0.002,
        ge=0,
        description="Cost reduction per $1 of R&D spending"
    )
    
    # ========== Firm Exit Parameters ==========
    loss_periods_to_exit: int = Field(
        default=6,
        ge=1,
        le=24,
        description="Number of consecutive loss periods before firm exits. 6 months reflects real-world firms using capital reserves to survive downturns."
    )
    
    # ========== Output Market Parameters ==========
    output_market_capacity: float = Field(
        default=0.0,
        ge=0,
        description="Market capacity Q_max for inverse demand. If 0, auto-scaled to 4x initial workforce."
    )
    output_price_intercept: float = Field(
        default=2.0,
        ge=0.1,
        description="Max willingness-to-pay (demand intercept). Must exceed wage for firm viability."
    )
    demand_growth_rate: float = Field(
        default=0.03,
        ge=0.0,
        le=0.2,
        description="Annual rate at which output market capacity grows (new products, markets, export demand). Reflects Say's Law: productivity gains create new demand over time."
    )
    
    # ========== New Task Creation (Acemoglu-Restrepo mechanism) ==========
    human_task_floor: float = Field(
        default=0.40,
        ge=0.0,
        le=0.8,
        description="Minimum share of effective labor that must come from humans (oversight, creativity, physical presence, relationship management). Based on OECD estimates that ~40-50% of tasks genuinely require human judgment, creativity, or physical presence."
    )
    new_task_creation_rate: float = Field(
        default=0.002,
        ge=0.0,
        le=0.05,
        description="Monthly rate at which new human-requiring tasks emerge as the economy grows (AI trainers, oversight roles, creative tasks). Represents Acemoglu-Restrepo reinstatement effect."
    )
    human_task_floor_max: float = Field(
        default=0.65,
        ge=0.0,
        le=0.9,
        description="Maximum value the human task floor can grow to via new task creation. Reflects that most complex tasks ultimately need human involvement."
    )
    
    # ========== Simulation Parameters ==========
    simulation_periods: int = Field(
        default=240,
        ge=12,
        le=1200,
        description="Number of periods to simulate (240 = 20 years monthly)"
    )
    random_seed: int = Field(
        default=42,
        description="Random seed for reproducibility"
    )
    
    # ========== Output Parameters ==========
    output_log_frequency: int = Field(
        default=12,
        ge=1,
        description="Frequency of logging metrics (e.g., 1 = every period, 12 = annually)"
    )
    save_full_agent_history: bool = Field(
        default=False,
        description="Save complete agent state each period (memory intensive)"
    )
    
    # ========== Behavior Toggles (for complexity control) ==========
    use_worker_heterogeneity: bool = Field(
        default=False,
        description="Enable worker skill heterogeneity (low-skill vs high-skill)"
    )
    use_firm_learning: bool = Field(
        default=False,
        description="Enable firms adaptive learning (vs static optimization)"
    )
    use_wage_bargaining: bool = Field(
        default=False,
        description="Enable wage bargaining (vs firm wage-posting)"
    )
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


# Default configuration instance
DEFAULT_CONFIG = SimulationConfig()


def create_custom_config(**kwargs) -> SimulationConfig:
    """Create a custom config by overriding defaults.
    
    Usage:
        config = create_custom_config(num_firms=5, initial_human_workers=2000)
    """
    config_dict = DEFAULT_CONFIG.dict()
    config_dict.update(kwargs)
    return SimulationConfig(**config_dict)
