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

### 2.3 Wage Adjustment (Phillips Curve)

$$\Delta W = -1.0 \cdot (u - u_{NAIRU}) - 0.1 \cdot AI_{share}$$

- Responds to unemployment gap and AI adoption
- Adjustment speed: 0.5 monthly

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

---

## 3. Agent Architecture

### 3.1 Firm Agent (`src/agents/firm.py`)

**Attributes**: firm_id, productivity, ai_adoption_level, capital, workforce, job_openings, wages_posted, R&D projects, accumulated R&D, age

**Key Methods**:
- `compute_labor_demand()` — CES elasticity of substitution
- `produce_output()` — Handles edge cases (zero labor)
- `compute_profits()` — Revenue minus labor costs
- `post_wages_and_vacancies()` — Strategic wage setting with markup
- `make_r_and_d_decision(current_period)` — Endogenous R&D choice
- `apply_lagged_r_and_d_benefits(current_period)` — 2-period lag application
- `check_exit_condition()` — Bankruptcy logic
- `step()` — Orchestrates full period

### 3.2 Worker Agent (`src/agents/worker.py`)

**Attributes**: worker_id, skill_level, status (employed/unemployed/entrepreneur), current_firm, current_wage, unemployment_duration, savings, reservation_wage

**Key Methods**:
- `receive_job_offer()` — Job acceptance logic
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
 2. Update market wage via Phillips curve
 3. Update worker reservation wages
 4. Process firm exits and separate workers
 5. Process entrepreneurship and new firm entry
 6. Execute worker steps (separations, unemployment)
 7. Clear job market
 8. Firms post wages and job vacancies
 9. Workers apply to jobs
10. Matching and employment allocation
11. Production and profit calculation
12. R&D decisions + lagged benefit application
13. Collect metrics
```

### Market Clearing

- Firms post both human and AI jobs (unlimited AI supply at cost)
- Workers apply stochastically (2–3 applications per search)
- Matching function allocates jobs respecting firm capacities

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
│   ├── job_market.py # Job posting, application, matching
│   ├── matching.py   # Cobb-Douglas matching function
│   ├── wage_dynamics.py    # Phillips curve
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
| `ai_productivity_multiplier` | 1.5 | AI productivity relative to human |
| `ai_wage_ratio` | 0.5 | AI cost / human wage |
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
| `ai_productivity` | 1.5× | Conservative estimate |
| `ai_wage_ratio` | 0.5× | Reflects hardware/electricity costs < human labor |
| `match_elasticity` | 0.5 | Standard in labor economics literature |
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
- Matching function applied after firm hiring decisions
- Phillips-curve style wage adjustment with AI dampening
- If vacancies > qualified labor, rationing by draw

### Agent Heterogeneity
- Firm heterogeneity: initially limited (random initial productivity)
- Worker heterogeneity: toggleable skill levels (low/high)
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
