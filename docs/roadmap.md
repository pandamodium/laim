# LAIM Roadmap

Remaining implementation work, building on the completed foundation (Phases 1–6) and the macroeconomic realism mechanisms.

**Current Status**: Phases 1–6 complete. Macroeconomic realism (demand growth, new task creation, AI augmentation, gradual adoption) implemented. Full 6-scenario analysis operational with economically coherent results. Phases 7–8 partially implemented.

---

## Completed Phases

- **Phase 1**: Foundation — Core agents (Firm, Worker, AI)
- **Phase 2**: Market Integration — JobMarket, SimulationEngine, matching
- **Phase 3**: Business Formation — Entrepreneurship, firm entry/exit
- **Phase 4**: AI Adoption & Innovation — R&D with lagged benefits
- **Phase 5**: Advanced Economics — Policies, skills, AI cost curves
- **Phase 5+**: Competitive Wages — MPL-based posting, poaching, superstar firms
- **Phase 6**: Macroeconomic Realism — Demand growth, new task creation, AI augmentation, gradual adoption, policy integration

---

## Phase 6: Comprehensive Metrics & Analytics ✅ (Partially)

### 6.1 Metrics Collection — ✅ Done

Current metrics per period: `period`, `num_firms`, `num_employed_human`, `num_employed_ai`, `num_unemployed`, `unemployment_rate`, `avg_wage_human`, `total_output`, `total_profit`, `job_vacancies`, `job_matches`, `new_firms_entered`, `firms_exited`, `avg_firm_size`.

### 6.2 Remaining Metrics Work

**Labor Market Metrics**:
- Unemployment by skill level / job category
- Job finding rates by group
- Wage distributions (mean, median, std, Gini)
- Wage inequality indices (Theil, Atkinson)

**Technology Metrics**:
- AI adoption rate by firm and sector
- R&D spending by firm
- Productivity indices (human vs AI)
- Technology diffusion speed

**Firm Metrics**:
- Firm entry/exit rates
- Firm size distribution
- Profit distribution
- Markup indices

**Macro Metrics**:
- Output per worker (labor productivity)
- Capital stock evolution
- Wage share of output
- Consumption (welfare proxy)

**Policy Metrics** (when enabled):
- UI recipients count, spending
- Retraining graduates, success rate
- Subsidy spending, tax credit claims

### 6.2 Data Export

- CSV export: quarterly summary, firm-level panel data, optional worker-level panel
- Parquet export for large simulations
- Results class with Pandas DataFrame interface and built-in summary statistics

### 6.3 Summary Statistics

- Descriptive statistics for all metrics
- Correlation matrices
- Regression output: wage on AI adoption, employment on firm productivity, R&D spending determinants
- Decomposition analysis: unemployment gap (by skill), wage growth (productivity vs. supply)

---

## Phase 7: Visualization & Interactive Dashboards

### 7.1 Static Plots (Matplotlib + Seaborn)

**Time Series**: unemployment rate, wage levels (aggregate + by skill), output/productivity, AI adoption rate, R&D spending

**Distributions**: wage histogram/violin, firm size distribution, employment by sector, worker skill distribution

**Cross-Section**: wage vs. education scatter, firm size vs. AI adoption, R&D vs. profitability

**Comparisons**: policy vs. baseline, high-AI vs. low-AI scenarios, skill groups side-by-side

### 7.2 Interactive Dashboard (Plotly)

- **Overview Tab**: Key macro metrics, current period status, policy summary
- **Labor Market Tab**: Interactive unemployment/wage time series, skill-level metrics, wage distribution evolution, job creation/destruction flows
- **Technology Tab**: AI adoption by firm (heatmap, time series), R&D spending dynamics, productivity vs. displacement trade-off
- **Firm Dynamics Tab**: Entry/exit flows, firm size distribution, profitability, market concentration
- **Policy Analysis Tab**: Policy impact on unemployment, participation rates, cost-benefit analysis
- **Scenario Comparison Tab**: Side-by-side policy comparisons, sensitivity analysis visualization, parameter sweep results

---

## Phase 8: Full Integration, Benchmarking & Validation

### 8.1 End-to-End Tests

- 20-year simulation completes without errors, all metrics calculated
- Constraint validation: employment ≤ labor supply, unemployment rate ∈ [0, 1], wages > 0
- Economic sanity: avg unemployment 3–6%, wage growth correlated with productivity, labor share 60–70%, AI adoption increases over time
- Phase interactions: business formation + R&D, policies + labor market, metrics consistency
- Reproducibility: same seed → same results

### 8.2 Benchmark Simulations ✅ Done

| Scenario | Description |
|----------|-------------|
| **No AI** | Counterfactual: AI useless and expensive |
| **Moderate AI** | Current trajectory: productivity 1.5×, cost 0.5× |
| **Aggressive AI** | Rapid progress: productivity 3×, cost 0.25×, high elasticity |
| **AI as Complement** | Low substitutability (σ=0.5): AI augments rather than replaces |
| **Aggressive AI + Policy** | High AI + retraining + subsidies + R&D credits |
| **Superstar Economy** | High AI + high firm dispersion (winner-take-most) |

All scenarios use `num_firms=10`, `simulation_periods=240`, `random_seed=42`.

### 8.3 Remaining Benchmark Work

### 8.3 Remaining Benchmark Work

**Sensitivity Analysis** — Parameters to sweep:
- `num_firms` (3, 5, 10, 20)
- `ai_productivity_multiplier` (1.2, 1.5, 2.0, 3.0)
- `human_task_floor` (0.20, 0.30, 0.40, 0.50)
- `demand_growth_rate` (0.01, 0.03, 0.05)
- `ai_adoption_speed` (0.02, 0.05, 0.10, 0.20)
- `ai_augmentation_factor` (0.1, 0.3, 0.5)
- `new_task_creation_rate` (0.0, 0.001, 0.002, 0.005)
- `firm_productivity_dispersion` (0.0, 0.3, 0.5, 1.0)
- `loss_periods_to_exit` (2, 4, 6, 12)

Output: sensitivity matrices, tornado diagrams, spider plots

### 8.4 Future Research Extensions

- **Sectoral heterogeneity**: Multiple sectors with different AI exposure (routine vs creative)
- **International trade**: Open economy with import competition and export demand
- **Wealth inequality**: Track wealth distribution, not just wages
- **Transition dynamics**: More granular modeling of retraining pathways
- **Generational effects**: Young vs old workers with different adaptation capabilities
- **Network effects**: Firm-to-firm supply chains and knowledge spillovers
