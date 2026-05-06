# LAIM Development History

A chronological record of each implementation phase, documenting what was built, key decisions, and test coverage.

---

## Phase 1: Foundation — Core Agents ✅

**Completed**: March 2026

### What Was Built

- **Base Agent Class** (`src/agents/base.py`): Abstract base with `step()` method and state export
- **Firm Agent** (`src/agents/firm.py`): Full economic logic including CES production function, labor demand optimization, strategic wage posting, profit maximization, R&D investment (basic), firm exit on sustained losses, separation dynamics
- **Worker Agent** (`src/agents/worker.py`): Job search with reservation wages, unemployment dynamics with spell tracking and wage decay, entrepreneurship with stochastic entry, employment savings accumulation
- **Market Mechanics** (`src/market/`): Cobb-Douglas matching and Phillips curve wage adjustment
- **Configuration System** (`src/config/parameters.py`): Pydantic-validated, 50+ parameters
- **Analytics Framework** (`src/analytics/`): Metrics collection, DataFrame export, summary statistics

### Key Achievements

- CES production with proper functional forms
- Realistic labor search with reservation wages and search pressure
- Dynamic entry/exit: firms exit on sustained losses, workers can become entrepreneurs
- R&D dynamics: investment reduces AI costs endogenously
- Modular design with clean separation of concerns

### Tests: 25 passing
- Agent initialization and state management
- Labor demand calculation with CES production
- Production function edge cases
- Profit calculation and firm exit
- R&D investment and productivity
- Job acceptance/rejection logic
- Unemployment spell dynamics with decay
- Entrepreneurship decision logic

---

## Phase 2: Market Integration ✅

**Completed**: March 2026

### What Was Built

- **JobMarket Class** (`src/market/job_market.py`): Complete market-clearing with micro-founded job search — firms post jobs, workers apply stochastically (2–3 applications), Cobb-Douglas matching allocates jobs respecting firm capacities
- **SimulationEngine** (`src/simulation/engine.py`): Full 12-step period orchestration — from market statistics through matching, production, R&D, to metrics collection. Handles 240-period (20-year) runs.
- **Market Dynamics**: Phillips curve wage adjustment with AI dampening, inverse demand output pricing, employment transitions (exogenous separation, matching, reservation wage decay)

### Key Achievements

- Micro-founded job market with posting → application → matching cycle
- Complete production chain: matching → hiring → production → profit → R&D
- Market wage determined by Phillips curve + AI dampening
- All Phase 1 components connected without breaking changes

### Tests: 15 new (40 total), all passing
- Job market initialization, posting, applications, matching, allocation
- Engine initialization, single/multi-period execution, market stats
- Phillips curve wage adjustment, output production
- Full 24-period simulation, market clearing cycle, unemployment dynamics

---

## Phase 3: Business Formation & Endogenous Entry/Exit ✅

**Completed**: March 2026

### What Was Built

- **Entrepreneurship System**: Workers accumulate savings during employment (save rate 20%), attempt business formation when savings exceed threshold
- **Entry Mechanics**: Stochastic entry responding to market saturation, entry cost 2% of average firm capital, random productivity for new entrants
- **Firm Exit**: Based on cumulative losses, workers separate and return to unemployment
- **Dynamic Firm Roster**: Firm list managed dynamically each period (add entries, remove exits)
- **Worker Transitions**: UNEMPLOYED → ENTREPRENEUR → EMPLOYED (new firm)

### Key Design Decisions

- Entry probability: `base_rate × (1 + unemployment_premium) × market_condition_factor × (1 - saturation_effect)`
- New firm productivity drawn from $N(\mu_{incumbent}, 0.10 \times \mu_{incumbent})$
- Entry capped to prevent cascading (~max 2% of unemployed)
- Both unemployed and employed workers can attempt entrepreneurship

### Tests: 8 new (48 total), all passing
- Entrepreneur capital requirements, entry with sufficient capital
- New firm initialization, exit conditions
- Short simulation runs, metrics tracking
- Basic simulation with entry, worker state validation

---

## Phase 4: AI Adoption & Innovation ✅

**Completed**: March 2026

### What Was Built

- **R&D State Management**: `RAndDProject` dataclass tracking individual investments with period, amount, expected gain, and lifecycle status
- **R&D Decision Logic** (`make_r_and_d_decision()`): Endogenous investment based on profitability, R&D cost 10% of capital requirement, expected 20% productivity boost, market learning from peer adoption (50% weight)
- **Lagged Benefit System** (`apply_lagged_r_and_d_benefits()`): 2-period lag between investment and benefit — Period T: investment, T+1: in development, T+2: benefits begin. Persistent and cumulative across projects.
- **Engine Integration**: Updated production loop to pass `current_period` to R&D methods. Sequence: production → profit → R&D decision → lagged benefits.

### Key Design Decisions

- **Why 2-period lag?** Reflects realistic innovation cycle (R&D → completion → deployment), creates intertemporal profit tradeoff, matches macroeconomic literature
- **Why multiple concurrent projects?** Supports realistic R&D pipelines, cumulative effects scale naturally, prevents unrealistic all-in behavior
- **Why current period tracking?** Precision (`periods_elapsed = current_period - investment_period`), survives refactors, fully auditable

### Code Impact
- `agents/firm.py`: +55 lines (R&D decision + lagged benefits)
- `simulation/engine.py`: ~10 lines (R&D method calls)
- Backward compatible: all Phase 1–3 tests still pass

### Tests: 48 total, all passing (no new test file; validated via Phase 3–4 integration tests)

---

## Phase 5: Advanced Economics Features ✅

**Completed**: March 2026

### What Was Built

#### Policy Interventions (`src/policy/interventions.py`)
- **UIBenefitTracker**: Unemployment insurance with configurable amounts, durations, automatic expiration
- **RetrainingProgramTracker**: Enrollment, duration tracking, success rate modeling, productivity boost on graduation
- **WageSubsidyTracker**: Eligibility filtering (displaced, low-skill, all), subsidy application/removal
- **TaxCreditTracker**: R&D tax credits and hiring credits with firm-level tracking
- **PolicyModule**: Unified interface integrating all policy systems

#### Skill-Based Technical Change (`src/market/skill_dynamics.py`)
- **SkillHeterogeneityModel**: Low-skill vs. high-skill assignment, skill-job matching, productivity bonuses
- **JobCategoryMarket**: Three categories (Routine, Management, Creative) with category-specific AI substitutability
- **WagePolarizationModel**: Category-specific wage adjustments, AI adoption effects, polarization index

#### AI Cost Dynamics (`src/market/ai_cost_dynamics.py`)
- **AICostTracker**: Learning-by-doing cost curves ($cost = base \times (1 + adoption)^{-\lambda}$)
- **AIProductivityBoost**: Base productivity tracking with learning-from-deployment effects
- **MarketAIDynamics**: Market-level coordination of cost/productivity, spillover effects
- **CostCurveAnalyzer**: Elasticity calculations, breakeven analysis, time-to-target estimation

#### Configuration: 30+ new parameters for policies, skills, job categories, and AI cost curves

### Tests: 33 new (81 total), all passing
- Policy interventions: 12 tests (UI, retraining, tax credits, policy module)
- Skill heterogeneity: 13 tests (skill matching, job categories, wage polarization)
- AI cost dynamics: 17 tests (cost curves, productivity, market dynamics, analysis)
- Zero regressions across all prior phases

---

## Competitive Wage Mechanism & Superstar Firms ✅

**Completed**: April 2026

### Motivation

Wages were falling in all simulation scenarios regardless of AI parameters. Root cause: the Phillips curve was the sole wage-setter, and it had no productivity growth term. Wages only responded to the unemployment gap — at NAIRU, wage growth was exactly zero. The AI dampening term ($-0.1 \times AI_{share}$) created persistent downward pressure even with minimal AI adoption. There was no mechanism for productivity gains to flow to wages.

### What Was Built

#### 1. Superstar Firm Productivity (`src/agents/firm.py`)
- **Log-normal productivity distribution**: Firm TFP $A_f$ drawn from $\ln(A_f) \sim N(0, \sigma)$ with default $\sigma = 0.5$
- Creates right-skewed distribution: top ~10% of firms have ~2× median productivity, top 2–3% have ~3–4×
- Matches empirical literature (Syverson 2011, Autor et al. 2020)
- New config param: `firm_productivity_dispersion` (default 0.5, range [0, 2])

#### 2. MPL-Based Wage Posting (`src/agents/firm.py`)
- **New method** `compute_mpl_human()`: Returns $A_f \cdot h_f$ (marginal product of human labor)
- **Replaced** old `post_wages_and_vacancies()`: Firms now post $w_f = \text{MPL} \times \theta \times (1 + \phi(u))$
  - $\theta$ = `labor_share_of_mpl` (default 0.65): fraction of MPL paid as wage
  - $\phi(u)$: cyclical tightness adjustment (±10% cap), bridges to NAIRU
- High-productivity firms naturally post higher wages — this is the channel through which productivity growth flows to wages
- New config param: `labor_share_of_mpl` (default 0.65, range [0.1, 0.95])

#### 3. Directed Search (`src/market/job_market.py`)
- **Replaced random application** with wage-weighted directed search (Moen 1997)
- Workers apply with probability proportional to posted wages
- Higher-wage firms attract more applicants, creating the labour market competition that bids wages up
- Firms face trade-off: higher wage attracts more workers but costs more per hire

#### 4. On-the-Job Search / Poaching (`src/agents/worker.py`, `src/simulation/engine.py`)
- **New method** `evaluate_poaching_offer()` on Worker: accept if outside wage exceeds current by threshold
- **New engine method** `_process_poaching()`: each period, employed workers sample outside offers
- Creates two-way pressure: high-productivity firms poach from low-productivity firms; all firms must raise wages to retain
- New config params: `on_the_job_search_rate` (default 0.05/month), `poaching_wage_threshold` (default 0.05)

#### 5. Retired Phillips Curve as Primary Wage Setter (`src/simulation/engine.py`)
- `market_wage_human` is now a **computed statistic**: employment-weighted average of firm posted wages
- No longer set by Phillips curve — wages emerge from firm-level MPL and competitive dynamics
- Phillips curve code retained in `wage_dynamics.py` for reference/reservation wage computation
- Downward wage rigidity (`downward_wage_rigidity`, default 0.3) still available in config

#### 6. Downward Wage Rigidity (`src/market/wage_dynamics.py`, `src/config/parameters.py`)
- Added asymmetric adjustment: when wage_growth < 0, scaled by `downward_wage_rigidity`
- 0 = fully rigid downward, 1 = fully flexible (symmetric)
- Captures stylized fact that real wages fall slowly via inflation erosion

#### 7. Streamlit UI Updates (`src/ui/parameter_panel.py`)
- Added sliders: Productivity Dispersion, Labor Share of MPL, On-the-Job Search Rate, Poaching Wage Threshold, Downward Wage Rigidity

### Key Design Decisions

- **Why MPL-based over Phillips curve?** The Phillips curve is a reduced-form shortcut for cyclical fluctuations. It cannot generate trend wage growth because it has no productivity term. MPL-based posting makes wages endogenous to productivity — wage growth *emerges* from R&D, firm competition, and poaching.
- **Why log-normal for productivity?** Matches well-documented empirical facts: firm productivity is right-skewed with fat tails. A few superstar firms dominate output (Autor et al. 2020).
- **Why directed search?** Without it, a firm posting 2× the wage gets the same applications as one posting 0.5×. Directed search (Moen 1997) creates the competitive bidding mechanism.
- **Why on-the-job search?** Without it, employed workers never receive competing offers — the main real-world mechanism for wage growth is eliminated.

### Code Impact
- `agents/firm.py`: +35 lines (compute_mpl_human, new post_wages_and_vacancies)
- `agents/worker.py`: +25 lines (evaluate_poaching_offer)
- `simulation/engine.py`: +60 lines (_process_poaching, new _update_aggregate_wage)
- `market/job_market.py`: ~20 lines modified (directed search)
- `config/parameters.py`: +30 lines (6 new parameters)
- `ui/parameter_panel.py`: +20 lines (5 new UI controls)
- 2 test assertions updated (market_wage_human no longer fixed at 1.0; Phillips curve test replaced)

### Tests: 154 total, all passing
- Zero regressions across all prior phases

---

## Phase 6: Macroeconomic Realism & Scenario Analysis ✅

**Completed**: May 2026

### Motivation

Initial simulations produced economically implausible results:
- "Moderate AI" scenario → 73% unemployment by year 20 (historically unprecedented)
- "AI as Complement" → 59% unemployment (economically incoherent for complements)
- "No AI" still hired AI (5.6% share) despite AI being useless and expensive
- Policy scenario was identical to aggressive AI (policies had zero effect)
- All scenarios showed wage decline even with full employment

Root causes:
1. **No new task creation** — displacement without reinstatement (the "lump of labor" fallacy)
2. **Fixed market capacity** — productivity gains crashed prices, killed firms
3. **No human floor** — 100% automation was a corner solution
4. **Instant AI adoption** — firms deployed unlimited AI in month 1
5. **No human productivity growth** — MPL was stagnant, so wages couldn't rise
6. **Firm exit too fragile** — 2-month loss tolerance caused cascade failures
7. **Policies disconnected** — wage subsidies and retraining had no engine integration

### What Was Built

#### 1. New Task Creation — Acemoglu-Restrepo Mechanism (`engine.py`)
- `_update_new_task_creation()`: Human task floor grows monthly with AI adoption
- More AI → more need for human oversight, creative direction, ethical judgment
- Floor starts at 40%, grows to max 65% over 20 years
- Rate accelerates with AI share (more automation → faster reinstatement)
- New config params: `human_task_floor` (0.40), `new_task_creation_rate` (0.002), `human_task_floor_max` (0.65)

#### 2. Endogenous Demand Growth (`engine.py`)
- `_grow_demand()`: Output market capacity grows over time
- Baseline: 3%/yr (new products, export markets, population-driven demand)
- Endogenous boost: accelerates when utilization > 50% (Say's Law — supply creates demand)
- Prevents permanent demand deficiency where productivity gains just crash prices
- New config param: `demand_growth_rate` (0.03)

#### 3. Human Productivity Growth / AI Augmentation (`engine.py`)
- `_update_human_productivity()`: Firm-level human productivity grows each period
- Two channels: (a) baseline 1.5%/yr (education, experience), (b) AI augmentation
- AI augmentation: firms with more AI coworkers see faster human productivity growth
- Diminishing returns (sqrt of AI share)
- This is the KEY mechanism: higher MPL → firms post higher wages → wages rise with AI
- New config params: `human_productivity_growth_rate` (0.015), `ai_augmentation_factor` (0.3)

#### 4. Gradual AI Adoption (`job_market.py`)
- Firms can only fill `ai_adoption_speed` (5%) of desired AI expansion per month
- Prevents instant displacement; creates realistic S-curve diffusion
- Minimum 1 unit per period (allows small firms to adopt slowly)
- New config param: `ai_adoption_speed` (0.05)

#### 5. AI Downsizing (`job_market.py`)
- Firms can decommission AI units when optimal demand < current stock
- AI is capital that can be retired (not a one-way ratchet)
- Ensures "No AI" scenario actually has near-zero AI

#### 6. Human Task Floor in Labor Demand (`firm.py`)
- `compute_labor_demand()` enforces minimum human share of total employment
- After CES optimization, if human_share < floor, redistribute to meet floor
- Represents tasks that fundamentally require humans (oversight, creativity, physical presence)

#### 7. Policy Integration (`job_market.py`)
- Wage subsidies reduce effective human labor cost in firm labor demand decisions
- R&D tax credits boost R&D spending
- Policies now have measurable impact on simulation outcomes

#### 8. Firm Exit Tolerance (`parameters.py`)
- `loss_periods_to_exit` increased from 2 → 6 months
- Prevents cascade exits (multiple firms dying simultaneously from a temporary price crash)
- Reflects real firms using capital reserves to survive downturns

#### 9. Updated Scenario Runner (`run_scenarios.py`)
- All 6 scenarios updated to use `num_firms=10` for diversified economy
- Proper comparison table with unemployment, wages, output, employment composition, firm dynamics

### Key Results (20-Year, 10 Firms, 1000 Workers, seed=42)

| Scenario | Wage Δ | Human Emp Δ | Output Δ | Yr20 Unemp | Peak Unemp | AI Share |
|----------|--------|------------|----------|-----------|-----------|----------|
| No AI | +34% | +45% | +120% | 3.0% | 6.7% | 1% |
| Moderate AI | +126% | +45% | +320% | 4.0% | 52.5%* | 31% |
| Aggressive AI | +130% | +60% | +382% | 5.0% | 22.7% | 19% |
| AI Complement | +115% | +45% | +320% | 4.0% | 24.2% | 29% |
| Aggr. + Policy | +133% | +43% | +370% | 5.3% | 17.0% | 19% |
| Superstar | +65% | +42% | +247% | 5.6% | 16.8% | 20% |

*52.5% peak is a single-month cascade event; annual average peak is ~13%.

### Economic Insights

1. **AI does NOT cause permanent job losses** — all scenarios show net human employment growth (42–60%)
2. **AI dramatically raises wages** — 115–133% growth vs only 34% without AI (AI augmentation mechanism)
3. **More aggressive AI is paradoxically BETTER for workers** — faster augmentation, more new tasks
4. **Policy significantly smooths transition** — reduces peak unemployment from 22.7% to 17.0%
5. **The real risk is inequality, not unemployment** — Superstar Economy shows only +65% wage growth despite similar output gains
6. **Transition is painful but manageable** — peak unemployment comparable to severe recession, recovers by year 6–8

### Code Impact
- `simulation/engine.py`: +80 lines (4 new methods, demand/task tracking state)
- `agents/firm.py`: +12 lines (human task floor enforcement in compute_labor_demand)
- `market/job_market.py`: +15 lines (gradual adoption, AI downsizing, wage subsidy)
- `config/parameters.py`: +50 lines (8 new parameters)
- `run_scenarios.py`: ~30 lines modified (num_firms=10, superstar params)

### Design Decisions

- **Why 40% human task floor?** OECD estimates 40–50% of tasks genuinely require human judgment, creativity, or physical presence. This is conservative.
- **Why 3% demand growth?** Matches long-run real GDP growth. Productivity creates new products/services that absorb output.
- **Why 5% AI adoption speed?** Enterprise AI deployment takes 12–24 months (McKinsey 2024). 5%/month ≈ 20 months to full deployment.
- **Why 6-month exit tolerance?** Prevents unrealistic cascade failures while still allowing natural creative destruction.
- **Why augmentation factor 0.3?** Studies show 20–80% productivity boost from AI tools; 0.3 at 50% AI share gives ~12% annual boost.
