# LAIM Roadmap

Remaining implementation work for phases 6–8, building on the completed foundation (Phases 1–5).

**Current Status**: Phases 1–5 complete (81 tests passing). Phases 6–8 partially implemented.

---

## Phase 6: Comprehensive Metrics & Analytics

### 6.1 Metrics Collection

Expand metrics beyond current level to enable detailed analysis.

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

### 8.2 Benchmark Simulations

| Scenario | Description |
|----------|-------------|
| **Baseline** | No policy, default parameters, 240 periods |
| **High AI** | AI productivity 2.0× (vs 1.5×), AI cost 0.3× (vs 0.5×) |
| **Policy** | UI at 60%, retraining active, R&D tax credit 25% |
| **Sectoral Shift** | Unequal AI exposure across sectors |

### 8.3 Sensitivity Analysis

Parameters to sweep:
- `num_firms` (2, 3, 5, 10)
- `ai_productivity_multiplier` (1.2, 1.5, 2.0, 3.0)
- `r_and_d_lag_periods` (1, 2, 3, 4)
- `entrepreneurship_rate` (0.02, 0.05, 0.10)
- `matching_efficiency` (0.5, 1.0, 1.5)

Output: sensitivity matrices, tornado diagrams, spider plots

### 8.4 Documentation & Publication

- **Technical Manual** (30–40 pages): model description, equations, parameters, implementation, calibration & validation
- **User Guide** (10–15 pages): installation, running simulations, interpreting results, common use cases
- **Economics Paper** (20–30 pages): research question, literature review, model and results, policy implications
- **Results Package**: 10–15 key tables, 15–20 publication-ready figures
