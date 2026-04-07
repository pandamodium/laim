# LAIM Architecture & Design Reference

**Project**: AI Labor Market Simulation (LAIM)
**Last Updated**: April 2026

---

## 1. Overview

LAIM is an agent-based model (ABM) of labor market dynamics with AI adoption. The simulation models oligopolistic firms competing for labor (human and AI), endogenous business formation, and R&D-driven productivity improvements.

### Core Research Questions

1. How does AI adoption affect human employment, wages, and unemployment?
2. What is the role of firm market power and oligopolistic competition?
3. How does R&D investment affect equilibrium outcomes?
4. What is the role of entrepreneurship ("animal spirits") in offsetting displacement?
5. What wage/employment dynamics emerge in steady state?

---

## 2. Economic Model

### 2.1 Production Function (CES)

$$Y = A[\alpha L_H^{-\sigma} + (1-\alpha) L_{AI}^{-\sigma}]^{-1/\sigma}$$

- Elasticity of substitution: $\sigma = 1.5$ (configurable)
- Supports zero labor edge cases

### 2.2 Labor Matching (Cobb-Douglas)

$$M = A \cdot U^{\alpha} \cdot V^{1-\alpha}$$

- $U$ = unemployment, $V$ = job vacancies
- Efficiency: $A$ = `matching_efficiency` (default 1.0)
- Elasticity: $\alpha = 0.5$

### 2.3 Wage Determination (MPL-Based Competitive)

Wages are set endogenously through firm-level competition, not a centralized Phillips curve.

**Firm wage posting (MPL-based)**:
$$w_f = \text{MPL}_H^f \times \theta \times (1 + \phi(u))$$

where:
- $\text{MPL}_H^f = A_f \cdot h_f$ is firm $f$'s marginal product of human labor
- $\theta$ = `labor_share_of_mpl` (default 0.65) — fraction of MPL paid as wage
- $\phi(u) = -0.5 \cdot (u - u_{NAIRU})$ — cyclical tightness adjustment (capped at ±10%)

**Directed search** (Moen 1997): Workers apply with probability proportional to posted wages. Higher-wage firms attract more applicants.

**On-the-job search (poaching)**: Employed workers sample outside offers at rate `on_the_job_search_rate` (default 5%/month). Switch if outside wage exceeds current by `poaching_wage_threshold` (default 5%). This creates competitive upward pressure on wages as productivity grows.

**Market wage**: Computed as employment-weighted average of firm posted wages (a statistic, not an input).

**Downward rigidity**: When firm MPL implies a wage cut, the adjustment is scaled by `downward_wage_rigidity` (default 0.3 = wages fall at 30% the speed they rise).

### 2.4 Output Pricing (Inverse Demand)

$$P = \max(1 - Q/Q_{max},\ 0.1)$$

- $Q_{max} = 100$ (market saturation)
- Floor prevents negative prices

### 2.5 Firm Exit

Firms exit after cumulative losses exceeding 2 periods of profit.

### 2.6 R&D & Innovation

- **Lagged Benefits**: 2-period lag between R&D investment and productivity gains
- **R&D Cost**: 10% of capital requirement
- **Productivity Boost**: 20% output multiplier per project
- **Market Learning**: Social learning from peer adoption (50% weight)
- **Multiple Projects**: Concurrent R&D projects with cumulative benefits

### 2.7 AI Cost Dynamics

- Learning-by-doing: $cost = base \times (1 + adoption)^{-\lambda}$, $\lambda = 0.3$
- R&D-driven cost reduction independent of adoption curve
- Both effects stack multiplicatively

### 2.8 Skill-Biased Technical Change

| Job Category | AI Substitutability | Wage Effect |
|-------------|-------------------|-------------|
| Routine | High (2.0×) | Downward pressure |
| Management | Medium (0.5×) | Moderate |
| Creative | Low (0.1×) | Complement/upward |

### 2.9 Firm Productivity Distribution (Superstar Firms)

Firm productivity $A_f$ is drawn from a log-normal distribution:
$$\ln(A_f) \sim N(0,\ \sigma_{\text{prod}})$$

With default $\sigma_{\text{prod}} = 0.5$ (`firm_productivity_dispersion`), the top ~10% of firms have ~2× median productivity and the top 2–3% have ~3–4×. This matches the empirical literature on firm productivity dispersion (Syverson 2011, Autor et al. 2020 "superstar firms").

---

## 3. Agent Architecture

### 3.1 Firm Agent (`src/agents/firm.py`)

**Attributes**: firm_id, productivity, ai_adoption_level, capital, workforce, job_openings, wages_posted, R&D projects, accumulated R&D, age

**Key Methods**:
- `compute_labor_demand()` — CES elasticity of substitution
- `compute_mpl_human()` — Marginal product of human labor ($A_f \cdot h_f$)
- `produce_output()` — Handles edge cases (zero labor)
- `compute_profits()` — Revenue minus labor costs
- `post_wages_and_vacancies()` — MPL-based wage posting with cyclical adjustment
- `make_r_and_d_decision(current_period)` — Endogenous R&D choice
- `apply_lagged_r_and_d_benefits(current_period)` — 2-period lag application
- `check_exit_condition()` — Bankruptcy logic
- `step()` — Orchestrates full period

### 3.2 Worker Agent (`src/agents/worker.py`)

**Attributes**: worker_id, skill_level, status (employed/unemployed/entrepreneur), current_firm, current_wage, unemployment_duration, savings, reservation_wage

**Key Methods**:
- `receive_job_offer()` — Job acceptance logic
- `evaluate_poaching_offer()` — On-the-job search: accept outside offer if wage premium exceeds threshold
- `update_unemployment_spell()` — Duration tracking with reservation wage decay
- `consider_entrepreneurship()` — Stochastic business entry
- `step()` — Coordinates worker behavior each period

### 3.3 AI Agent (`src/agents/ai_agent.py`)

Simplified pooled tracking — AI agents are not individual, tracked at firm level as employment quantity and cost per unit.

---

## 4. Simulation Engine (`src/simulation/engine.py`)

### Period Step Cycle

```
Period t Flow:
 1. Compute market statistics (unemployment, vacancies)
 2. Update market wage (employment-weighted avg of firm posted wages)
 3. Update worker reservation wages
 4. Execute worker steps (separations, unemployment)
 5. Clear job market
 6. Firms post wages (MPL-based) and job vacancies
 7. Workers apply via directed search (wage-weighted)
 8. Matching and employment allocation
 8b. On-the-job search / poaching
 9. Production and profit calculation
10. R&D decisions + lagged benefit application
11. Process firm exits
12. Process entrepreneurship and new firm entry
13. Collect metrics
```

### Market Clearing

- Firms post both human and AI jobs (unlimited AI supply at cost)
- Workers apply via directed search — probability proportional to posted wage
- Cobb-Douglas matching function determines match count; allocation respects firm capacities
- Employed workers may receive outside offers (poaching) and switch if premium exceeds threshold

---

## 5. Module Organization

```
src/
├── agents/           # Agent classes
│   ├── base.py       # Abstract base class
│   ├── firm.py       # Firm agent (CES production, R&D)
│   ├── worker.py     # Worker agent (job search, entrepreneurship)
│   └── ai_agent.py   # Pooled AI tracking
├── market/           # Market mechanics
│   ├── job_market.py # Job posting, directed search, matching
│   ├── matching.py   # Cobb-Douglas matching function
│   ├── wage_dynamics.py    # Reservation wage computation (Phillips curve retained for reference)
│   ├── skill_dynamics.py   # Skill heterogeneity & wage polarization
│   └── ai_cost_dynamics.py # Learning-by-doing cost curves
├── simulation/
│   ├── engine.py     # Main SimulationEngine class
│   ├── benchmarks.py # Benchmark scenario runner
│   └── validation.py # Constraint validation
├── analytics/
│   ├── metrics.py              # Results tracking
│   ├── comprehensive_metrics.py # Extended analytics
│   ├── dashboard.py            # Interactive dashboards
│   ├── plots.py                # Static plots
│   └── visualization.py       # Plotting utilities
├── policy/
│   └── interventions.py  # UI, retraining, subsidies, tax credits
└── config/
    └── parameters.py     # 80+ validated Pydantic parameters
```

### Dependency Graph

```
main.py → SimulationEngine → [agents, market, simulation]
SimulationEngine → analytics
agents → config
market → config
analytics → config
policy → config
```

---

## 6. Configuration & Parameters

All parameters live in `src/config/parameters.py` (Pydantic-validated, single source of truth).

### Core Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_firms` | 3 | Oligopolistic firms |
| `initial_human_workers` | 1000 | Labor supply |
| `human_population_growth_rate` | 0.02 | Annual growth |
| `firm_substitution_elasticity` | 1.5 | Human-AI elasticity |
| `firm_productivity_dispersion` | 0.5 | Log-normal σ for superstar firms |
| `labor_share_of_mpl` | 0.65 | Fraction of MPL offered as wage |
| `ai_productivity_multiplier` | 1.5 | AI productivity relative to human |
| `ai_wage_ratio` | 0.5 | AI cost / human wage |
| `on_the_job_search_rate` | 0.05 | Monthly poaching probability |
| `poaching_wage_threshold` | 0.05 | Min premium to switch firms |
| `downward_wage_rigidity` | 0.3 | Asymmetric wage adjustment (0=rigid, 1=flex) |
| `base_entrepreneurship_rate` | 0.05 | Business formation rate |
| `r_and_d_profit_share` | 0.05 | R&D allocation |
| `matching_efficiency` | 1.0 | Cobb-Douglas efficiency |
| `simulation_periods` | 240 | Periods (240 = 20 years monthly) |

### Policy Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ui_replacement_rate` | 0.50 | UI as % of wage |
| `ui_benefit_duration_periods` | 26 | Weeks of UI coverage |
| `retraining_program_enabled` | false | Toggle retraining |
| `retraining_cost` | 5000 | Cost per worker |
| `wage_subsidy_enabled` | false | Enable wage subsidies |
| `r_and_d_tax_credit_enabled` | false | Enable R&D tax credits |

### AI & Skill Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_skill_heterogeneity` | false | Enable skill levels |
| `skill_distribution_low_share` | 0.50 | % low-skill workers |
| `use_job_categories` | false | Enable job categories |
| `ai_cost_curve_learning_enabled` | false | Enable learning curves |
| `ai_cost_learning_parameter` | 0.3 | Learning steepness λ |

### Parameter Justification

| Parameter | Baseline | Justification |
|-----------|----------|---------------|
| `num_firms` | 3 | Small enough for visible dynamics, large enough for competition |
| `initial_human_workers` | 1000 | Large enough for meaningful statistics |
| `firm_productivity_dispersion` | 0.5 | Matches Syverson (2011) TFP dispersion; creates 2–4× superstar firms |
| `labor_share_of_mpl` | 0.65 | Empirical labor share of income ~60–70% |
| `ai_productivity` | 1.5× | Conservative estimate |
| `ai_wage_ratio` | 0.5× | Reflects hardware/electricity costs < human labor |
| `match_elasticity` | 0.5 | Standard in labor economics literature |
| `on_the_job_search_rate` | 0.05 | ~5% monthly job-to-job transition rate (Fallick & Fleischman 2004) |
| `poaching_wage_threshold` | 0.05 | Workers need 5% premium to switch (mobility friction) |
| `downward_wage_rigidity` | 0.3 | Real wages fall slowly via inflation erosion |
| `entrepreneurship_rate` | 0.05 | Kauffman survey average ~3–5% |
| `r_and_d_profit_share` | 0.05 | Typical for technology firms |

---

## 7. Design Decisions & Trade-offs

### Computational Complexity
- Vectorized NumPy operations for agent batches
- Job pool matching (aggregate level) rather than pair-wise search
- Agent state stored in pandas DataFrames for efficient operations
- Start with ~1000 agents on monthly time-step

### Market Clearing & Frictions
- MPL-based firm wage posting with cyclical tightness adjustment
- Directed search: workers apply proportionally to posted wages (Moen 1997)
- On-the-job search: employed workers receive outside offers, creating poaching dynamics
- Cobb-Douglas matching function for job allocation
- Downward wage rigidity: wages fall at a fraction of the speed they rise

### Agent Heterogeneity
- Firm heterogeneity: log-normal productivity distribution (superstar firms)
- Worker heterogeneity: toggleable skill levels (low/high)
- Wage dispersion: emerges endogenously from firm productivity dispersion
- Simplified decision rules (static best-response, threshold rules)
- Configuration flags toggle complexity features

### R&D Lag Design
- **Why 2-period lag?** Reflects realistic innovation cycle (R&D → completion → deployment), creates intertemporal profit tradeoff, matches macroeconomic literature
- **Why multiple projects?** Supports realistic R&D pipelines, prevents "spend everything on R&D" behavior
- **Why not depreciation?** Period-based lag is more transparent and matches economic theory better

### Business Formation
- Entry probability: `base_rate × (1 + profit_signal) × exp(-market_saturation)`
- New firm productivity drawn from $N(\mu_{incumbent}, 0.10 \times \mu_{incumbent})$
- Entry capped to prevent cascading (~max 2% of unemployed becoming entrepreneurs)

---

## 8. Validation & Calibration Strategy

### Empirical Targets (Monthly Equivalents)

| Target | Expected Range |
|--------|---------------|
| Unemployment rate | 4–5% |
| Job finding rate | 15–20% (Shimer 2012) |
| Wage growth | 0.2–0.3% per month (2.4–3.6% annual) |
| Beveridge curve | Negative UV correlation |
| Labor share of income | 60–70% |

### Constraint Validation
- Total employment ≤ labor supply
- Total firm output ≥ 0
- Wage growth correlated with labor scarcity
- Unemployment rate ∈ [0%, 100%]

### Sensitivity Analysis
Built-in parameter sweep framework for systematic analysis across `num_firms`, `ai_productivity_multiplier`, `r_and_d_lag_periods`, `entrepreneurship_rate`, and `matching_efficiency`.

---

## 9. Research Applications

### Labor Economics
- Technology adoption timing and labor displacement
- Wage polarization from skill-biased technical change
- Unemployment dynamics during automation transitions
- Worker retraining effectiveness

### Industrial Organization
- R&D investment decisions under uncertainty
- Innovation race behavior in oligopolistic markets
- Firm growth and exit under technology competition
- Productivity heterogeneity and market selection

### Macroeconomics
- Aggregate productivity growth from technology diffusion
- Sectoral reallocation and structural change
- Fiscal policy responses to automation unemployment
- Wage-inflation dynamics with automation

### Inequality
- Income distribution evolution during transitions
- Early-adopter advantage in technology races
- Wealth concentration from R&D success
- Sectoral inequality (routine vs. creative work)
