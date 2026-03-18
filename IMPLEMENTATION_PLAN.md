# AI Labor Market Simulation: Implementation Plan

**Last Updated**: March 18, 2026

## Executive Summary

This document outlines the architecture, design decisions, and implementation strategy for an agent-based model (ABM) of labor market dynamics with AI adoption. The simulation models oligopolistic firms competing for labor (human and AI), endogenous business formation, and R&D-driven productivity improvements.

---

## 1. Project Overview & Objectives

### Core Research Questions
1. How does AI adoption affect human employment, wages, and unemployment?
2. What is the role of firm market power and oligopolistic competition?
3. How does R&D investment affect equilibrium outcomes?
4. What is the role of entrepreneurship ("animal spirits") in offsetting displacement?
5. What wage/employment dynamics emerge in steady state?

### Key Features
- **Oligopolistic Firms** (default 3) with:
  - Production functions (CES with human and AI labor)
  - Profit maximization
  - R&D investment with productivity spillovers
  - Pricing power in output markets
  
- **Labor Supply**:
  - Human workers (default 1000) with slow exogenous growth
  - Unemployment dynamics and job search
  - Reservation wages and skill matching
  - Entrepreneurial entry thresholds
  
- **AI Labor**:
  - Unlimited aggregate supply with endogenous adoption
  - Lower wage but different productivity profile
  - Costs affected by firm R&D
  
- **New Business Formation**:
  - Exogenous entrepreneurship ("animal spirits") from unemployed and employed
  - Entry competition with incumbent firms
  - Heterogeneous entrepreneur productivity

---

## 2. Potential Issues & Solutions

### Issue 1: Computational Complexity
**Problem**: With continuous agent updates, simulation could be slow.

**Solutions**:
- Use vectorized NumPy operations for agent batches
- Implement job pool matching (aggregate level) rather than pair-wise search
- Store agent state in pandas DataFrames for efficient operations
- Cache market-level aggregates between periods
- Profile code early to identify bottlenecks

**Implementation**: Start with ~1000 agents on a monthly time-step; expand only if needed.

---

### Issue 2: Market Clearing & Frictions
**Problem**: Unmatched workers and job openings create market pressure without adjustment mechanism.

**Solutions**:
- **Matching Function**: Use Cobb-Douglas matching: $M = A U^{\alpha} V^{1-\alpha}$ where:
  - $U$ = unemployment
  - $V$ = job vacancies
  - $A$ = matching efficiency
  - $\alpha$ = typical value 0.5
  
- **Wage Dynamics**:
  - Phillips-curve style wage adjustment: $\Delta w = f(\text{unemployment gap}, \text{AI share})$
  - Wages sluggish: adjust partially toward reservation level
  - AI adoption may suppress wage growth
  
- **Quantity Adjustment**: If vacancies > qualified labor, rationing by draw; firms post wages strategically

**Implementation**: Matching function applied after firm hiring decisions to determine actual matches.

---

### Issue 3: Agent Proliferation & Heterogeneity
**Problem**: Many agents create computational burden; decisions need to be realistic but simple.

**Solutions**:
- **Firm Heterogeneity**: Limited initially (all identical except random initial productivity)
- **Worker Heterogeneity**: Start simple (no skill differences), add later if needed
  - Binary skill level option: "high-skill" vs "low-skill"
  - AI substitutes better for low-skill workers
  
- **Simplified Decision Rules**:
  - Firms: Use simple optimization (static best-response) rather than learning
  - Workers: Use threshold rules for job acceptance/entrepreneurship entry
  
**Implementation**: Use configuration flags (`USE_WORKER_HETEROGENEITY`, `USE_FIRM_LEARNING`) to toggle complexity.

---

### Issue 4: Calibration & Parameter Sensitivity
**Problem**: Many parameters; unclear what values are realistic.

**Solutions**:
- **Baseline Calibration**:
  - Human productivity = 1.0 (numeraire)
  - AI productivity = 1.5x human
  - AI wage = 0.5x human wage (captures both cost reduction and no benefits)
  - Firm substitution elasticity ≈ 1.5 (slight substitutability but not perfect)
  - Matching efficiency $A$ set to match 15-20% monthly hires at baseline unemployment
  
- **Sensitivity Analysis Framework**: Built-in tools to sweep parameters and visualize outcomes

- **Validation**: Compare to empirical moments where possible (e.g., Beveridge curve)

**Implementation**: Store all parameters in `src/config/parameters.py` with documentation; easy sweep functionality.

---

### Issue 5: Business Formation Mechanics
**Problem**: How do we model "animal spirits" and entry realistically?

**Solutions**:
- **Entry Trigger**: Persons decide to start business with probability that depends on:
  - Current unemployment status (higher if unemployed)
  - Expected profitability (function of firm profits and market saturation)
  - Wealth accumulated (need minimum capital to start)
  - Entrepreneurial ability draw (heterogeneous)
  
- **Entry Model**:
  ```
  Entry Probability = base_rate × (1 + profit_signal) × exp(-market_saturation)
  ```
  
- **New Firm Characteristics**:
  - Productivity draw from distribution (e.g., normal with incumbent mean/std)
  - Enter at small initial scale (hire 0-5 workers initially)
  - Subject to same production function as incumbents
  
- **Exit Rule**: Firms earning losses for 2+ consecutive periods exit (simple rule)

**Implementation**:
1. Each period, sample from unemployment + employed willing to switch
2. For each potential entrant, draw profitability signal
3. Apply stochastic entry rule
4. New firms join oligopolistic competition

---

### Issue 6: R&D Spillovers & Productivity Growth
**Problem**: How do R&D investments translate to productivity/cost reductions?

**Solutions**:
- **Firm R&D Decision**:
  - Firms allocate portion of profits to R&D
  - R&D spending reduces AI wage (cost reduction) or increases AI productivity
  - Effect has lag (e.g., 2-period delay for R&D to commercialize)
  
- **Spillover Structure**:
  - Public spillovers: 50% of any firm's R&D productivity gain available to all firms
  - Private benefit: 50% benefit only the innovating firm
  - Creates incentive for innovation but also benefits competitors
  
- **Functional Form**:
  ```
  ΔAI_productivity = firm_R&D_share × R&D_efficiency × random_shock
  ΔAI_cost = -γ × accumulated_R&D / total_AI_employment
  ```

**Implementation**: Store cumulative R&D by firm; update productivity with lag; apply spillovers uniformly.

---

### Issue 7: Unemployment & Labor Market State
**Problem**: Need realistic unemployment dynamics without full job-search model.

**Solutions**:
- **Simple Unemployment Model**:
  - Employed workers separate at exogenous rate (~2% per period)
  - Unemployed workers receive job offers from matching function
  - Job acceptance based on offered wage vs reservation wage
  - Reservation wage depends on UI benefits, duration, expectations
  
- **Worker States**:
  - Employed (firm ID, wage, skill level)
  - Unemployed (spell duration, skill level)
  - Entrepreneurship consideration (accumulated savings, success threshold)

**Implementation**: Worker dataframe with state column; update states vectorized each period.

---

### Issue 8: Oligopoly Dynamics & Competition
**Problem**: Three firms need interaction mechanics; default Bertrand/Cournot?

**Solutions**:
- **Market Structure Options**:
  1. **Cournot Competition**: Firms choose quantities sequentially
     - Demand: Inverse demand $P = 1 - Q$ (linear)
     - Each firm best-responds to others' output
     - More realistic for heterogeneous labor costs
     
  2. **Wage Bertrand**: Firms compete on wages (posting) for workers
     - Workers apply to firms; allocate to best wage up to firm capacity
     - More aligned with modern labor market
     
  3. **Mixed (Recommended)**: 
     - Cournot in output quantities
     - Wage competition in labor (firms post wages, workers apply)
     - Separates commodity market power from labor market power

**Implementation**: 
- Use option flag for competition type
- Start with Cournot output but wage-post labor (separates dynamics)
- Firms solve static optimization each period

---

### Issue 9: Time-Step Granularity
**Problem**: Should periods be days, months, years?

**Solutions**:
- **Monthly Timescale** (Recommended):
  - Aligns with employment statistics (CPS, BLS)
  - 20-year simulation = 240 periods (manageable)
  - Wage/hiring changes can be meaningful month-to-month
  - Matches labor market data frequencies
  
- **Alternative**: Quarterly (80 periods for 20 years) if slower time needed

**Implementation**: Store period length in config; easy to convert between scales.

---

### Issue 10: Output & State Validation
**Problem**: How to ensure simulation produces sensible outcomes?

**Solutions**:
- **Sanity Checks**:
  - Total employment ≤ labor supply
  - Total firm output ≥ 0
  - Wage growth correlated with labor scarcity
  - Unemployment rate 0-100%
  
- **Validation Moments**:
  - Steady-state unemployment rate (compare to natural rate ~4.5%)
  - Wage growth (compare to productivity growth + inflation)
  - Labor share of income (typical ~65%)
  - Job openings to unemployed ratio (Beveridge curve)

**Implementation**: Unit tests for each constraint; monitoring dashboard during simulation.

---

## 3. Core Architecture

### 3.1 Agent Classes

#### **Firm Agent**
```python
class Firm:
    attributes:
        - firm_id: int
        - productivity: float (for both human and AI labor)
        - ai_adoption_level: float (0-1, intensity of AI use)
        - capital: float (accumulated wealth)
        - output_target: float
        - workforce: List[Worker] (human and AI workers employed)
        - job_openings: int
        - wages_posted: dict (human_wage, ai_cost)
        - R&D_spending: float (previous period)
        - accumulated_R&D: float (stock)
        - age: int (entry period)
    
    methods:
        - compute_labor_demand(output_target, wage_human, wage_ai)
        - post_wages_and_vacancies()
        - hire_workers(matched_candidates)
        - produce_output()
        - make_R&D_decision(profits)
        - compute_profits()
        - check_exit_condition()
```

#### **Worker Agent**
```python
class Worker:
    attributes:
        - worker_id: int
        - skill_level: str ("low", "high")
        - status: str ("employed", "unemployed", "entrepreneur")
        - current_firm: int or None
        - current_wage: float
        - unemployment_duration: int
        - savings: float
        - reservation_wage: float
        - entrepreneurship_success_prob: float
    
    methods:
        - receive_job_offer(firm_id, wage)
        - evaluate_job_offer(wage)
        - apply_to_firms(available_firms)
        - become_entrepreneur()
        - update_unemployment_spell()
        - update_reservation_wage()
```

#### **AI Agent (Simplified)**
```python
class AIAgent:
    # Simplified: AI agents are pooled, not individual
    # Tracked at firm level as employment and cost
    # No individual state needed
    
    attributes:
        - firm_id: int
        - quantity: int (number of AI units)
        - cost_per_unit: float
```

### 3.2 Matching Function
```python
def cobb_douglas_match(unemployment, vacancies, efficiency=1.0, elasticity=0.5):
    """
    Matches = efficiency * (unemployment^elasticity) * (vacancies^(1-elasticity))
    """
    return efficiency * (unemployment**elasticity) * (vacancies**(1-elasticity))
```

### 3.3 Market Cycle Logic (Each Period)

1. **Wage/Price Setting**:
   - Firms set posted wages for human labor
   - Firms set AI cost (endogenous to R&D)
   - Output prices determined by market demand

2. **Labor Demand**:
   - Firms compute optimal labor demand (human + AI) given wages
   - Post job vacancies

3. **Matching**:
   - Apply matching function to determine job matches
   - Allocate jobs to workers based on preferences

4. **Production**:
   - Firms produce output using hired labor
   - Revenue = output × price

5. **Business Formation**:
   - Sample potential entrepreneurs
   - Stochastic entry of new firms
   - Existing firms exit if losses persist

6. **R&D & Accumulation**:
   - Firms decide R&D spending from profits
   - Productivity/cost updated with lag
   - Spillovers applied

7. **Worker Separations**:
   - Exogenous job separations (workers become unemployed)
   - Workers update unemployment duration, reservation wages

8. **Data Collection**:
   - Record all metrics to database for analysis

---

## 4. Key Data Structures

### 4.1 Configuration (Pydantic Model)

```python
class SimulationConfig:
    # Firm parameters
    num_firms: int = 3
    firm_cobb_douglas_elasticity: float = 0.5  # human vs AI substitution
    
    # Labor supply
    initial_human_workers: int = 1000
    human_population_growth_rate: float = 0.02
    separation_rate_employed: float = 0.02
    
    # AI parameters
    ai_productivity_multiplier: float = 1.5
    ai_wage_ratio: float = 0.5
    ai_initial_share: float = 0.1
    
    # Entrepreneurship
    base_entrepreneurship_rate: float = 0.05
    entrepreneurship_unemployed_premium: float = 2.0
    min_capital_to_start: float = 10000.0
    
    # R&D
    r_and_d_profit_share: float = 0.05  # Firms allocate 5% profits to R&D
    r_and_d_efficiency: float = 0.01
    r_and_d_lag_periods: int = 2
    
    # Market matching
    matching_efficiency: float = 1.0
    matching_elasticity: float = 0.5
    
    # Simulation
    simulation_periods: int = 240  # 20 years monthly
    random_seed: int = 42
```

### 4.2 Output Database Schema

```python
# Recorded each period:
class PeriodMetrics:
    period: int
    num_firms: int
    num_employed_human: int
    num_employed_ai: int
    num_unemployed: int
    unemployment_rate: float
    avg_wage_human: float
    avg_wage_ai_cost: float
    total_output: float
    avg_firm_output: float
    total_firm_profits: float
    avg_firm_profits: float
    job_vacancies: int
    job_matches: int
    new_firms_entered: int
    firms_exited: int
    avg_ai_adoption: float
    ai_productivity_index: float
    human_productivity_index: float
    aggregate_r_and_d: float
    wage_inequality: float
    employment_share_human: float
    employment_share_ai: float
```

---

## 5. Implementation Sequence

### Phase 1: Foundation (Core Agents)
- [ ] Create base `Agent` parent class
- [ ] Implement `Firm` class with basic attributes
- [ ] Implement `Worker` class with state tracking
- [ ] Implement `SimulationConfig` and parameter validation

**Tests**: Unit tests for agent initialization and attribute updates

---

### Phase 2: Market Mechanics (Core Market)
- [ ] Implement matching function
- [ ] Implement firm labor demand optimization (static)
- [ ] Implement wage posting mechanism
- [ ] Implement job application/matching logic

**Tests**: Verify matching function properties; test wage equilibrium

---

### Phase 3: Production & Dynamics (Simulation Cycle)
- [ ] Implement production function (CES for labor)
- [ ] Implement profit calculation
- [ ] Implement job separations
- [ ] Implement basic unemployment dynamics

**Tests**: Monthly cycle produces sensible sequences (wages, employment, output)

---

### Phase 4: Business Formation (Entry/Exit)
- [ ] Implement entrepreneurship decision logic
- [ ] Implement new firm entry mechanics
- [ ] Implement firm exit mechanism
- [ ] Track firm survival dynamics

**Tests**: Entry rate reasonable; firm survival duration realistic

---

### Phase 5: R&D & Productivity (Innovation Dynamics)
- [ ] Implement firm R&D allocation
- [ ] Implement productivity growth from R&D
- [ ] Implement spillover effects
- [ ] Implement AI cost reduction

**Tests**: R&D spending correlates with firm size; productivity growth realistic

---

### Phase 6: Analytics & Output (Metrics)
- [ ] Implement comprehensive metrics tracking
- [ ] Implement data logging to database
- [ ] Create summary statistics calculation
- [ ] Build baseline diagnostic plots

**Tests**: Metrics database populated correctly; no missing values

---

### Phase 7: Visualization & Dashboard
- [ ] Create static plots (time series, distributions)
- [ ] Create interactive dashboard (Plotly)
- [ ] Implement export functions (CSV, charts)

**Tests**: Plots render without errors; all metrics represented

---

### Phase 8: Integration & Validation
- [ ] End-to-end simulation runs from config to output
- [ ] Long-run stability checks
- [ ] Sensitivity analysis framework
- [ ] Documentation and examples

**Tests**: Full 20-year simulation completes without errors

---

## 6. Parameter Baseline & Justification

| Parameter | Baseline | Justification |
|-----------|----------|---------------|
| `num_firms` | 3 | Oligopoly; small enough for dynamics visible, large enough for competition |
| `initial_human_workers` | 1000 | Allows scaling; large enough for statistics |
| `human_pop_growth` | 0.02 | ~2% annual growth, realistic for developed economies |
| `ai_productivity` | 1.5x | Conservative; faster learning for AI likely |
| `ai_wage_ratio` | 0.5x | Reflects hardware/electricity costs < human labor |
| `match_elasticity` | 0.5 | Standard in labor econ; balanced substitution |
| `entrepreneurship_rate` | 0.05 | ~5% annual; Kauffman survey avg ~3-5% |
| `r_and_d_profit_share` | 0.05 | ~5% of profits; typical for tech firms |

---

## 7. Validation & Calibration Strategy

### Empirical Targets (Monthly Equivalents)
- Unemployment rate: 4-5% range
- Job finding rate: 15-20% (matches Shimer 2012)
- Wage growth: 0.2-0.3% per month (2.4-3.6% annual)
- Beveridge curve: negative UV correlation

### Sensitivity Analysis Framework
```python
# Built-in utility:
def sweep_parameter(param_name, values, metric_names):
    """
    Run simulation for each value, return metrics.
    Creates heatmaps and sensitivity plots.
    """
```

---

## 8. Code Organization & Dependencies

### Imports Structure
```
src/
├── config/
│   └── parameters.py  ← All config; single source of truth
├── agents/
│   ├── __init__.py
│   ├── base.py  ← Base Agent class
│   ├── firm.py  ← Firm agent
│   ├── worker.py  ← Worker agent
│   └── ai_agent.py  ← AI pooled tracking
├── market/
│   ├── __init__.py
│   ├── matching.py  ← Matching function
│   └── wage_dynamics.py  ← Wage adjustment logic
├── simulation/
│   ├── __init__.py
│   ├── engine.py  ← Main SimulationEngine class
│   └── step_logic.py  ← Detailed period update logic
├── analytics/
│   ├── __init__.py
│   ├── metrics.py  ← Metrics collection
│   ├── database.py  ← Data storage/retrieval
│   └── visualization.py  ← Plotting utilities
└── main.py  ← Entry point
```

### Dependency Graph
```
main.py → SimulationEngine → [agents, market, simulation]
SimulationEngine → analytics
agents → config
market → config
analytics → config
```

---

## 9. Testing Strategy

### Unit Tests (`tests/`)
- `test_agents.py`: Agent initialization, state updates
- `test_market.py`: Matching function properties, wage dynamics
- `test_simulation.py`: Period update logic
- `test_config.py`: Config parsing and validation

### Integration Tests
- `test_full_simulation.py`: End-to-end run, check no crashes
- `test_constraints.py`: All sanity checks pass (employment ≤ supply, etc.)
- `test_steady_state.py`: Long-run properties (unemployment stabilizes, etc.)

### Diagnostic Checks
- Plot diagnostics after each major phase
- Compare metrics to empirical targets
- Inspect outliers and edge cases

---

## 10. Future Extensions (Beyond MVP)

1. **Worker Heterogeneity**: Skill distributions, learning effects
2. **Firm Learning**: Econometric learning, adaptation over time
3. **Multi-Sector**: Different industries with varying AI exposure
4. **Wage Bargaining**: Firm-worker bargaining instead of posting
5. **Social Networks**: Job finding through networks
6. **Policy Interventions**: UBI, training, wage subsidies
7. **Sectoral Shifts**: Reallocation across industries
8. **International Trade**: Offshoring, outsourcing

---

## 11. Software Engineering Best Practices

### Code Quality
- Type hints throughout (Python 3.9+)
- Docstrings for all classes/functions
- PEP 8 compliance
- Pre-commit hooks for linting

### Reproducibility
- All runs seed random numbers
- Full config exported with each run
- Version control for code and data
- Experiment tracking (parameters → outputs)

### Performance
- Profile early, optimize bottlenecks
- Vectorize where possible (pandas/numpy)
- Cache expensive computations
- Monitor memory for long runs

---

## Summary: Key Design Principles

1. **Modularity**: Agents, market, simulation are independent components
2. **Configurability**: All parameters in one place; easy sensitivity analysis
3. **Validation**: Sanity checks and empirical calibration built-in
4. **Transparency**: Output comprehensive metrics; trace individual agent decisions if needed
5. **Scalability**: Structure allows increasing agents without major refactoring
6. **Extensibility**: Base classes allow easy addition of new agent types or mechanisms

---

## Next Steps

1. Create base agent classes (Phase 1)
2. Implement matching function and wage dynamics (Phase 2)
3. Build simulation cycle and test on small example
4. Gradually add complexity (business formation, R&D, etc.)
5. Calibrate to empirical moments
6. Run sensitivity analysis
7. Document results and conclusions

