# AI Labor Market Simulation

An agentic framework for analyzing the macroeconomic impact of AI on labor markets through agent-based modeling. The simulation examines how oligopolistic firms, human workers, and AI agents interact in a dynamic labor market with endogenous business formation.

**Status**: ✅ Phase 5 Complete — 81/81 tests passing

## Features

- **Multi-Agent System**: Firms and workers with individual economic decision-making
- **Oligopolistic Competition**: 3 firms (configurable) with dynamic pricing
- **Labor Market Matching**: Micro-founded job search with Cobb-Douglas matching function
- **Wage Dynamics**: Phillips curve adjustment responding to unemployment and AI share
- **AI Adoption**: Endogenous R&D investment with 2-period lagged benefits and technology diffusion
- **Business Formation**: Entrepreneurship system with worker-to-firm transitions
- **Comprehensive Metrics**: Track hiring, unemployment, job openings, wages, firm dynamics, R&D pipelines
- **Extensible Framework**: Ready for policy analysis, international trade, inequality studies

## Quick Start

```python
from src.simulation.engine import SimulationEngine
from src.config.parameters import SimulationConfig

# Create and run simulation
config = SimulationConfig()  # 3 firms, 1000 workers, 240 periods
engine = SimulationEngine(config)
results = engine.run()

# Analyze results
print(f"Mean unemployment: {results['unemployment_rate'].mean():.1%}")
print(f"Final wage: ${results['avg_wage_human'].iloc[-1]:.2f}")
```

## Project Structure

```
ai_labor_market/
├── src/
│   ├── agents/           # Firm, Worker, AI agents
│   ├── market/           # Job market, matching, wage dynamics, skill & AI cost dynamics
│   ├── simulation/       # Engine, benchmarks, validation
│   ├── analytics/        # Metrics, dashboards, plots, visualization
│   ├── policy/           # UI, retraining, subsidies, tax credits
│   └── config/           # 80+ validated Pydantic parameters
├── tests/                # 81 tests (all passing)
├── docs/                 # Project documentation
│   ├── architecture.md   # System design, economic model, parameters
│   ├── development-history.md  # Phase-by-phase build record
│   └── roadmap.md        # Remaining work (Phases 6-8)
├── notebooks/            # Jupyter workflows
├── outputs/              # Results, dashboards, plots
└── requirements.txt
```

## Simulation Components

### Phase 1: Foundation ✅
- **Firm agent**: CES production, labor demand optimization, profit calculation, firm exit
- **Worker agent**: Job search, reservation wages, unemployment dynamics, entrepreneurship
- **Configuration**: 50+ validated Pydantic parameters
- **Testing**: 25 unit & integration tests

### Phase 2: Market Integration ✅
- **JobMarket class**: Job posting, application, Cobb-Douglas matching
- **SimulationEngine**: Full 12-step period orchestration
- **Market clearing**: Phillips curve wage adjustment with AI dampening
- **Demand**: Inverse demand pricing (P = 1 - Q/Q_max, floor 0.1)
- **Testing**: 15 integration tests for market dynamics

### Phase 3: Business Formation ✅
- **Entrepreneurship system**: Workers start firms with accumulated savings
- **Entry mechanics**: Stochastic entry responding to market saturation
- **New firm initialization**: Random productivity, entry period tracking
- **Dynamic firm list**: Firms enter and exit based on profitability
- **Worker transitions**: UNEMPLOYED → ENTREPRENEUR → EMPLOYED (new firm)
- **Exit handling**: Workers separate on firm exit, return to unemployment
- **Testing**: 8 optimized tests (1.6 seconds runtime)

### Phase 4: AI Adoption & Innovation ✅
- **R&D Decision System**: Firms make endogenous choices about AI investment based on profitability
- **Lagged Benefits**: 2-period lag between R&D investment and productivity gains (realistic innovation cycle)
- **R&D Pipeline**: Track individual R&D projects from investment → development → deployment
- **AI Adoption Mechanics**: Gradual firm-level AI adoption with worker displacement
- **Multiple R&D Projects**: Firms can maintain concurrent projects with cumulative benefits
- **Market Integration**: Productivity effects aggregate to firm and market productivity
- **Testing**: 8 integration tests (Phase 3-4 combined, all passing)

## Configuration

Edit `src/config/parameters.py` or pass parameters to `SimulationConfig()`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_firms` | 3 | Oligopolistic firms |
| `initial_human_workers` | 1000 | Labor supply |
| `human_population_growth_rate` | 0.02 | Annual growth |
| `firm_substitution_elasticity` | 1.5 | Human-AI elasticity |
| `ai_productivity_multiplier` | 1.5 | AI productivity relative to human |
| `ai_wage_ratio` | 0.5 | AI cost/human wage |
| `base_entrepreneurship_rate` | 0.05 | Business formation rate |
| `r_and_d_profit_share` | 0.05 | R&D allocation |
| `matching_efficiency` | 1.0 | Cobb-Douglas efficiency |
| `simulation_periods` | 240 | Periods (240 = 20 years monthly) |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/test_market_integration.py -v

#With coverage
pytest tests/ --cov=src --cov-report=html
```

**Status**: 81/81 tests passing ✅
- Phase 1: 25 tests (agents, configuration, basic market)
- Phase 2: 15 tests (job market, simulation engine, dynamics)
- Phase 3-4: 16 tests (business formation, AI adoption, integration)
- Phase 5: 33 tests (policies, skills, AI cost curves)
- **Runtime**: ~2 seconds total

## Running Simulations

```python
# Basic 20-year simulation with defaults
engine = SimulationEngine(SimulationConfig())
results = engine.run()
print(results.head())

# Custom configuration
config = SimulationConfig(
    num_firms=5,
    initial_human_workers=2000,
    simulation_periods=120  # 10 years
)
engine = SimulationEngine(config)
results = engine.run()

# Results DataFrame has 14 metrics per period
print(results.columns)
# ['period', 'num_firms', 'num_employed_human', 'num_employed_ai', 
#  'num_unemployed', 'unemployment_rate', 'avg_wage_human', 'total_output', 
#  'total_profit', 'job_vacancies', 'job_matches', 'new_firms_entered', 
#  'firms_exited', 'avg_firm_size']
```

## Economic Model

### Production Function (Firm)
- **CES Production**: Y = A[αL_H^(-σ) + (1-α)L_AI^(-σ)]^(-1/σ)
- Elasticity of substitution: σ = 1.5 (configurable)
- Supports zero labor edge cases

### Labor Matching (Market)
- **Cobb-Douglas**: M = A·U^α·V^(1-α)
- Efficiency: A = matching_efficiency (default 1.0)
- Elasticity: α = 0.5 (unemployment elasticity)

### Wage Adjustment (Phillips Curve)
- ΔW = -1.0·(u - u_NAIRU) - 0.1·AI_share
- Responds to unemployment gap and AI adoption
- Adjustment speed: 0.5 monthly

### Pricing
- **Inverse Demand**: P = max(1 - Q/Q_max, 0.1)
- Q_max = 100 (market saturation)
- Floor prevents negative prices

### Firm Exit
- On cumulative losses > 2 periods of profit

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Streamlit Dashboard

The interactive dashboard lets you configure parameters, run simulations, compare scenarios, and explore results visually.

```bash
# From the ai_labor_market/ directory
streamlit run app.py
```

This opens the app in your browser (default `http://localhost:8501`). From the dashboard you can:

- **Configure parameters** — adjust firm count, labor supply, AI settings, CES elasticity, policy levers, etc.
- **Run simulations** — execute with live progress streaming
- **Compare scenarios** — save named scenarios and view side-by-side comparisons
- **Browse past runs** — reload results from `outputs/runs/`
- **Export data** — download metrics as CSV

### Phase 5: Advanced Economics ✅
- **Policy Interventions**: UI benefits, retraining programs, wage subsidies, tax credits
- **Skill-Based Technical Change**: Job categories (Routine/Management/Creative) with differential AI substitutability
- **AI Cost Dynamics**: Learning-by-doing cost curves, R&D-driven cost reduction, spillover effects
- **Testing**: 33 tests for policies, skills, and AI cost curves

## Documentation

- **[docs/architecture.md](docs/architecture.md)**: System design, economic model, parameters, validation strategy
- **[docs/development-history.md](docs/development-history.md)**: Phase-by-phase implementation record
- **[docs/roadmap.md](docs/roadmap.md)**: Remaining work (Phases 6–8)

## Key Design Features

✓ **CES Production Function** - Human-AI substitution elasticity = 1.5  
✓ **Cobb-Douglas Matching** - Micro-founded job search  
✓ **Phillips Curve** - Wage response to unemployment + AI  
✓ **Oligopolistic Firms** - Cournot-style output competition  
✓ **Parsimony** - Monthly time-steps (240 periods = 20 years)  
✓ **Extensibility** - Clean agent/market/simulation separation  
✓ **Modularity** - Easy to add skills, sectors, policies  

## Dependencies

- `numpy` - Numerical computing
- `pandas` - Data analysis
- `pydantic` - Configuration validation
- `pytest` - Testing
- `matplotlib`, `plotly` - Visualization (partial)
- `scipy` - Scientific computing

See `requirements.txt`.

## Next Steps

See [docs/roadmap.md](docs/roadmap.md) for remaining work:
- **Phase 6**: Comprehensive metrics & analytics (inequality indices, data export, regressions)
- **Phase 7**: Visualization & interactive dashboards (static plots, Plotly dashboard)
- **Phase 8**: Full integration, benchmarking & validation (end-to-end tests, sensitivity analysis)

## License

Research use.
