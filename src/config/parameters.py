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
    separation_rate_employed: float = Field(
        default=0.02,
        ge=0,
        le=1,
        description="Monthly exogenous job separation rate (workers become unemployed)"
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
        le=2,
        description="AI cost-per-unit as ratio of human wage (captures hardware + electricity)"
    )
    ai_initial_adoption_share: float = Field(
        default=0.1,
        ge=0,
        le=1,
        description="Initial AI employment share (as fraction of total workforce)"
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
        default=10000.0,
        ge=0,
        description="Minimum accumulated savings needed to start business"
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
    ui_replacement_rate: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Unemployment insurance as fraction of previous wage"
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
    
    # ========== Firm Exit Parameters ==========
    loss_periods_to_exit: int = Field(
        default=2,
        ge=1,
        le=12,
        description="Number of consecutive loss periods before firm exits"
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
        description="Enable firmsadaptive learning (vs static optimization)"
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
