# LAIM Architecture & Design Reference

**Project**: AI Labor Market Simulation (LAIM)
**Last Updated**: May 2026

---

## 1. Overview

LAIM is an agent-based model (ABM) of labor market dynamics with AI adoption. The simulation models oligopolistic firms competing for labor (human and AI), endogenous business formation, R&D-driven productivity improvements, new task creation, and growing demand.

### Core Research Questions

1. Does AI lead to permanent job losses, or does it follow the historical pattern of net job creation?
2. How does AI adoption affect human employment, wages, and unemployment over a 20-year horizon?
3. What is the role of new task creation (Acemoglu & Restrepo) in offsetting displacement?
4. How does growing demand (Say's Law) prevent permanent demand deficiency?
5. What is the role of AI augmentation in raising human productivity and wages?
6. How do policy interventions (retraining, subsidies) affect the transition?
7. Does the "superstar economy" (high firm dispersion) create inequality more than unemployment?

---

## 2. Economic Model

### 2.1 Production Function (Additive with CES Allocation)

$$Y = A \cdot (L_H + m \cdot L_{AI})$$

- $A$ = firm-specific TFP (log-normal draw)
- $m$ = `ai_productivity_multiplier` (default 1.5)
- Labor allocation between H and AI via CES first-order condition:

$$\frac{L_{AI}}{L_H} = \left(\frac{1-\alpha}{\alpha}\right)^\sigma \cdot \left(\frac{w_H}{c_{AI}/m}\right)^\sigma$$

- Elasticity of substitution: $\sigma$ = `firm_substitution_elasticity` (default 1.5)
- $\alpha = 0.6$ (human share weight)
- **Human task floor**: $\min(L_H / (L_H + L_{AI})) \geq$ `human_task_floor` (default 0.40)

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

### 2.4 Output Pricing (Inverse Demand with Growth)

$$P = a \cdot \left(1 - \frac{Q}{Q_{max}(t)}\right), \quad P \geq 0.1$$

- $a$ = `output_price_intercept` (default 2.0)
- $Q_{max}(t)$ grows endogenously:
  - Baseline: 3%/yr (`demand_growth_rate`)
  - Endogenous boost: accelerates when utilization > 50% (new products absorb output)
- Initial $Q_{max} = 4 \times$ `initial_human_workers` (auto-scaled)

### 2.5 Firm Exit

Firms exit after `loss_periods_to_exit` (default 6) consecutive months of losses. This reflects real-world firms using capital reserves to survive downturns.

### 2.6 New Task Creation (Acemoglu & Restrepo 2018)

As AI automates existing tasks, new tasks emerge that require human input:

$$\text{human\_task\_floor}(t+1) = \min\left(\text{max\_floor},\ \text{floor}(t) + r \cdot (1 + s_{AI})\right)$$

- $r$ = `new_task_creation_rate` (default 0.002/month)
- $s_{AI}$ = current AI employment share (higher AI → faster new task creation)
- Floor grows from 0.40 to max 0.65 (`human_task_floor_max`)
- Represents: AI oversight, creative direction, ethical judgment, relationship management, novel problem-solving

### 2.7 Human Productivity Growth (AI Augmentation)

Human MPL grows via two channels:

1. **Baseline growth**: 1.5%/yr from education, experience, general tech progress
2. **AI augmentation**: humans working alongside AI become more productive

$$h_f(t+1) = h_f(t) \cdot \left(1 + g_{base} + \frac{\lambda \cdot \sqrt{s_{AI}^f}}{12}\right)$$

- $g_{base}$ = monthly baseline growth (from 1.5% annual)
- $\lambda$ = `ai_augmentation_factor` (default 0.3)
- $s_{AI}^f$ = firm-level AI share (sqrt for diminishing returns)

This is the key mechanism through which AI RAISES wages: higher MPL → firms post higher wages.

### 2.8 Gradual AI Adoption

Firms cannot instantly deploy unlimited AI. Each period, they can fill at most `ai_adoption_speed` (default 5%) of the gap between desired and actual AI employment:

$$\Delta L_{AI} = \min\left(L_{AI}^* - L_{AI},\ \max(1,\ 0.05 \cdot (L_{AI}^* - L_{AI}))\right)$$

Reflects real-world frictions: integration complexity, infrastructure needs, organizational change.

AI can also be **decommissioned** when optimal demand falls below current stock.

### 2.9 R&D & Innovation

- **Lagged Benefits**: 2-period lag between R&D investment and productivity gains
- **R&D Allocation**: `r_and_d_profit_share` (5%) of profits allocated to R&D
- **Multiple Projects**: Concurrent R&D projects with cumulative benefits
- **AI Cost Reduction**: R&D reduces firm-level AI cost (diminishing returns, 80% cap)
- **AI Productivity Boost**: R&D raises firm AI productivity (capped at 3× base)

### 2.10 AI Cost Dynamics

- Learning-by-doing: $cost = base \times (1 + adoption)^{-\lambda}$, $\lambda = 0.3$
- R&D-driven cost reduction independent of adoption curve
- Both effects stack multiplicatively

### 2.11 Skill-Biased Technical Change (Optional)

| Job Category | AI Substitutability | Wage Effect |
|-------------|-------------------|-------------|
| Routine | High (2.0×) | Downward pressure |
| Management | Medium (0.5×) | Moderate |
| Creative | Low (0.1×) | Complement/upward |

### 2.12 Firm Productivity Distribution (Superstar Firms)

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
 4b. Reconcile firm headcounts
 5. Population growth (new labor force entrants)
 6. Demand growth (expanding market capacity)
 7. New task creation (Acemoglu-Restrepo: human floor grows with AI)
 8. Human productivity growth (baseline + AI augmentation)
 9. Clear job market
10. Firms post wages (MPL-based) and job vacancies
    - AI downsizing (if optimal < current)
    - Gradual AI adoption (speed-limited expansion)
    - Wage subsidy applied to effective human cost
11. Workers apply via directed search (wage-weighted)
12. Matching and employment allocation
12b. On-the-job search / poaching
13. Production and profit calculation (Cournot pricing)
14. R&D decisions + lagged benefit application
15. Process firm exits (6-month loss tolerance)
16. Process entrepreneurship and new firm entry
17. Collect metrics
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
| `num_firms` | 3 | Starting firms (use 10 for diversified economy) |
| `initial_human_workers` | 1000 | Labor supply |
| `human_population_growth_rate` | 0.02 | Annual labor force growth |
| `human_productivity_growth_rate` | 0.015 | Annual baseline human productivity growth |
| `ai_augmentation_factor` | 0.3 | AI coworker boost to human productivity |
| `firm_substitution_elasticity` | 1.5 | Human-AI elasticity (>1 = substitutes) |
| `firm_productivity_dispersion` | 0.5 | Log-normal σ for superstar firms |
| `labor_share_of_mpl` | 0.65 | Fraction of MPL offered as wage |
| `ai_productivity_multiplier` | 1.5 | AI productivity relative to human |
| `ai_wage_ratio` | 0.5 | AI cost / human wage |
| `ai_adoption_speed` | 0.05 | Max fraction of AI gap filled per month |
| `human_task_floor` | 0.40 | Min share of tasks requiring humans |
| `new_task_creation_rate` | 0.002 | Monthly rate new human tasks emerge |
| `demand_growth_rate` | 0.03 | Annual output market capacity growth |
| `on_the_job_search_rate` | 0.05 | Monthly poaching probability |
| `poaching_wage_threshold` | 0.05 | Min premium to switch firms |
| `downward_wage_rigidity` | 0.3 | Asymmetric wage adjustment (0=rigid, 1=flex) |
| `base_entrepreneurship_rate` | 0.05 | Business formation rate |
| `loss_periods_to_exit` | 6 | Months of losses before firm exit |
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
| `num_firms` | 3 (10 for scenarios) | 10 gives diversified economy; prevents cascade exits |
| `initial_human_workers` | 1000 | Large enough for meaningful statistics |
| `human_productivity_growth_rate` | 0.015 | US average annual productivity growth 1948–2024 |
| `ai_augmentation_factor` | 0.3 | Conservative: studies show 20–80% productivity boost from AI tools |
| `human_task_floor` | 0.40 | OECD estimates ~40–50% of tasks require human judgment/creativity |
| `new_task_creation_rate` | 0.002 | Calibrated so floor grows ~25% over 20 years |
| `demand_growth_rate` | 0.03 | Real GDP growth ~2–3% historically |
| `ai_adoption_speed` | 0.05 | Enterprise AI deployment takes 12–24 months (McKinsey 2024) |
| `loss_periods_to_exit` | 6 | Firms typically survive 6–12 months of losses before closure |
| `firm_productivity_dispersion` | 0.5 | Matches Syverson (2011) TFP dispersion |
| `labor_share_of_mpl` | 0.65 | Empirical labor share of income ~60–70% |
| `ai_productivity` | 1.5× | Conservative estimate of current AI capability |
| `ai_wage_ratio` | 0.5× | Reflects hardware/electricity costs < human labor |
| `match_elasticity` | 0.5 | Standard in labor economics literature |
| `on_the_job_search_rate` | 0.05 | ~5% monthly job-to-job transition rate (Fallick & Fleischman 2004) |
| `entrepreneurship_rate` | 0.05 | Kauffman survey average ~3–5% |

---

## 7. Design Decisions & Trade-offs

### Computational Complexity
- Vectorized NumPy operations for agent batches
- Job pool matching (aggregate level) rather than pair-wise search
- Agent state stored in pandas DataFrames for efficient operations
- Start with ~1000 agents on monthly time-step

### Macroeconomic Realism
- **Demand growth**: Output market capacity grows endogenously; prevents "lump of output" fallacy
- **New task creation**: Acemoglu-Restrepo mechanism prevents corner solution of full automation
- **AI augmentation**: Humans with AI tools are more productive; raises MPL and wages
- **Gradual adoption**: Implementation friction (5%/month) prevents instant displacement
- **Firm resilience**: 6-month loss tolerance prevents cascade exit events
- **AI downsizing**: Firms decommission AI when economics change (not just one-way ratchet)

### Market Clearing & Frictions
- MPL-based firm wage posting with cyclical tightness adjustment
- Directed search: workers apply proportionally to posted wages (Moen 1997)
- On-the-job search: employed workers receive outside offers, creating poaching dynamics
- Cobb-Douglas matching function for job allocation
- Downward wage rigidity: wages fall at a fraction of the speed they rise
- Wage subsidies: reduce effective human cost when policy enabled

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

| Target | Expected Range | Model Result (Moderate AI) |
|--------|---------------|---------------------------|
| Unemployment rate (steady state) | 3–5% | 3–4% (yr 6–20) |
| Peak transitional unemployment | 10–25% (comparable to recessions) | ~13% annual avg (yr 3) |
| Long-run wage growth (20yr) | 50–150% | +126% |
| Long-run employment growth | 30–60% (population + creation) | +45% |
| AI employment share (20yr) | 20–40% | 31% |
| Output growth (20yr) | 100–400% | +320% |
| Labor share of income | 60–70% | ~65% (from labor_share_of_mpl) |
| Firm entry/exit | Positive net entry | 223 entries, 69 exits |

### Constraint Validation
- Total employment ≤ labor supply
- Total firm output ≥ 0
- Wage growth correlated with labor scarcity
- Unemployment rate ∈ [0%, 100%]

### Sensitivity Analysis
Built-in parameter sweep framework for systematic analysis across `num_firms`, `ai_productivity_multiplier`, `r_and_d_lag_periods`, `entrepreneurship_rate`, and `matching_efficiency`.

---

## 9. Research Applications & Key Findings

### Summary of Findings (May 2026)

The model strongly supports the historical pattern: **AI, like every prior general-purpose technology, leads to net job creation and wage growth in the long run**, through a potentially painful transition period:

1. **No permanent job losses**: All scenarios show 42–60% human employment growth over 20 years
2. **AI raises wages significantly**: +115–133% wage growth vs only +34% without AI
3. **Transition is real but manageable**: Peak unemployment comparable to severe recession (13–22% annual), recovers by year 6–8
4. **The real risk is inequality**: Superstar economy shows only +65% wage growth vs +130% baseline
5. **Policy helps smooth the transition**: Reduces peak unemployment from 22.7% to 17.0%
6. **More aggressive AI is paradoxically better**: Faster augmentation, more new tasks, higher wages

### Labor Economics
- Technology adoption timing and labor displacement → **temporary, 3-5 year adjustment**
- Wage polarization from skill-biased technical change
- New task creation offsets displacement (Acemoglu & Restrepo mechanism confirmed)
- Worker retraining effectiveness → **measurable reduction in peak unemployment**

### Industrial Organization
- R&D investment decisions under uncertainty
- Firm entry/exit dynamics during technology transitions
- Superstar firm dynamics and market concentration
- Productivity heterogeneity and wage inequality (key risk factor)

### Macroeconomics
- Aggregate productivity growth from AI diffusion → **3–4× output growth**
- Demand creation (Say's Law) prevents permanent demand deficiency
- Fiscal policy responses to automation unemployment
- AI augmentation as driver of long-run wage growth

### Inequality
- Superstar economy: gains concentrate in high-productivity firms
- Income distribution: wages rise but unevenly across firm types
- Policy effectiveness: subsidies and retraining reduce transitional inequality
- **Key insight**: inequality, not unemployment, is the primary long-run risk from AI
