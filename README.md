# AI Labor Market Simulation

An agent-based model (ABM) for analyzing the macroeconomic impact of AI on labor markets. The simulation examines how oligopolistic firms, human workers, and AI agents interact in a dynamic labor market with endogenous business formation, new task creation, and growing demand.

**Status**: ✅ Phase 5+ Complete — Full scenario analysis operational

## Key Finding

> **AI does not lead to permanent job losses.** Across all simulated scenarios (moderate, aggressive, complement, policy), human employment grows 42–60% and real wages rise 65–133% over a 20-year horizon. The transition period involves temporary unemployment (peak ~13–22% annually), but the economy recovers through entrepreneurship, new task creation, and demand growth — matching the historical pattern of every prior general-purpose technology.

## Features

- **Multi-Agent System**: Firms and workers with individual economic decision-making
- **Oligopolistic Competition**: 10 firms (configurable) with Cournot output pricing
- **Labor Market Matching**: Micro-founded directed search with Cobb-Douglas matching function
- **Wage Dynamics**: MPL-based competitive wage posting with on-the-job search (poaching)
- **AI Adoption**: Gradual diffusion with implementation friction, endogenous R&D with lagged benefits
- **New Task Creation**: Acemoglu & Restrepo mechanism — new human-required tasks emerge as AI grows
- **Demand Growth**: Endogenous market expansion (Say's Law) prevents permanent demand deficiency
- **Human Productivity Growth**: AI augmentation raises MPL (humans with AI tools are more productive)
- **Human Task Floor**: Minimum share of tasks requiring human input (oversight, creativity, relationships)
- **Business Formation**: Entrepreneurship system with worker-to-firm transitions
- **Policy Interventions**: Wage subsidies, retraining programs, R&D tax credits (integrated into engine)
- **Comprehensive Metrics**: Track hiring, unemployment, wages, firm dynamics, AI adoption, R&D
- **6-Scenario Comparison**: No AI, Moderate, Aggressive, Complement, Policy, Superstar Economy

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

## Scenario Results (20-Year Horizon, 10 Firms, 1000 Workers)

| Scenario | Wage Growth | Human Emp Growth | Output Growth | Yr20 Unemployment | AI Share |
|----------|------------|-----------------|--------------|-------------------|----------|
| No AI (counterfactual) | +34% | +45% | +120% | 3.0% | 1% |
| Moderate AI | **+126%** | +45% | +320% | 4.0% | 31% |
| Aggressive AI | **+130%** | +60% | +382% | 5.0% | 19% |
| AI as Complement | +115% | +45% | +320% | 4.0% | 29% |
| Aggressive AI + Policy | **+133%** | +43% | +370% | 5.3% | 19% |
| Superstar Economy | +65% | +42% | +247% | 5.6% | 20% |

## Project Structure

```
ai_labor_market/
├── src/
│   ├── agents/           # Firm, Worker, AI agents
│   ├── market/           # Job market, matching, wage dynamics, skill & AI cost dynamics
│   ├── simulation/       # Engine, benchmarks, validation
│   ├── analytics/        # Metrics, dashboards, plots, visualization
│   ├── policy/           # UI, retraining, subsidies, tax credits
│   └── config/           # 90+ validated Pydantic parameters
├── tests/                # Unit & integration tests
├── docs/                 # Project documentation
│   ├── architecture.md   # System design, economic model, parameters
│   ├── development-history.md  # Phase-by-phase build record
│   └── roadmap.md        # Remaining work
├── notebooks/            # Jupyter workflows
├── outputs/              # Results, dashboards, plots, scenario analysis
│   └── scenario_analysis/  # 6-scenario comparison results
├── run_scenarios.py      # Main scenario runner (6 scenarios × 240 months)
└── requirements.txt
```

## Simulation Components

### Phase 1: Foundation ✅
- **Firm agent**: CES production, labor demand optimization, profit calculation, firm exit
- **Worker agent**: Job search, reservation wages, unemployment dynamics, entrepreneurship
- **Configuration**: 50+ validated Pydantic parameters

### Phase 2: Market Integration ✅
- **JobMarket class**: Job posting, directed search, Cobb-Douglas matching
- **SimulationEngine**: Full period orchestration
- **Market clearing**: MPL-based wage posting with on-the-job search
- **Demand**: Inverse demand pricing with growing market capacity

### Phase 3: Business Formation ✅
- **Entrepreneurship system**: Workers start firms with accumulated savings
- **Dynamic firm roster**: Entry via entrepreneurship, exit on sustained losses (6-month tolerance)

### Phase 4: AI Adoption & Innovation ✅
- **R&D Decision System**: Endogenous AI investment with 2-period lagged benefits
- **Gradual AI Adoption**: Implementation friction limits deployment speed (5%/month of gap)
- **AI Downsizing**: Firms can decommission AI units when economics change

### Phase 5: Advanced Economics ✅
- **Policy Interventions**: Wage subsidies, retraining programs, R&D tax credits
- **Skill Heterogeneity**: Low-skill vs high-skill with category-specific AI exposure
- **AI Cost Dynamics**: Learning-by-doing curves with R&D-driven cost reduction

### Phase 6: Macroeconomic Realism ✅ (May 2026)
- **New Task Creation**: Acemoglu-Restrepo mechanism — human task floor grows with AI adoption
- **Demand Growth**: Endogenous market expansion (3%/yr base + utilization response)
- **Human Productivity Growth**: AI augmentation raises MPL (1.5%/yr base + AI coworker boost)
- **Gradual AI Diffusion**: Implementation friction prevents instant displacement
- **Policy Integration**: Wage subsidies reduce effective human cost in firm labor decisions

## Configuration

Edit `src/config/parameters.py` or pass parameters to `SimulationConfig()`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_firms` | 3 | Starting firms (use 10 for realistic diversification) |
| `initial_human_workers` | 1000 | Labor supply |
| `human_population_growth_rate` | 0.02 | Annual labor force growth |
| `human_productivity_growth_rate` | 0.015 | Annual baseline productivity growth |
| `ai_augmentation_factor` | 0.3 | How much AI coworkers boost human productivity |
| `firm_substitution_elasticity` | 1.5 | Human-AI elasticity (>1 = substitutes) |
| `ai_productivity_multiplier` | 1.5 | AI productivity relative to human |
| `ai_wage_ratio` | 0.5 | AI cost/human wage |
| `ai_adoption_speed` | 0.05 | Max fraction of AI gap filled per month |
| `human_task_floor` | 0.40 | Min share of tasks requiring humans |
| `new_task_creation_rate` | 0.002 | Monthly rate new human tasks emerge |
| `demand_growth_rate` | 0.03 | Annual output market capacity growth |
| `loss_periods_to_exit` | 6 | Months of losses before firm exit |
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

**Status**: Tests passing ✅
- Phase 1: 25 tests (agents, configuration, basic market)
- Phase 2: 15 tests (job market, simulation engine, dynamics)
- Phase 3-4: 16 tests (business formation, AI adoption, integration)
- Phase 5: 33 tests (policies, skills, AI cost curves)
- **Runtime**: ~2 seconds total

## Running Scenarios

The primary way to use this tool is via the scenario runner:

```bash
# Run all 6 scenarios (takes ~30 seconds)
python run_scenarios.py
```

This produces:
- Individual CSV results for each scenario in `outputs/scenario_analysis/`
- A combined comparison table printed to stdout
- Summary statistics CSV

```python
# Or run programmatically with custom parameters
from src.simulation.engine import SimulationEngine
from src.config.parameters import SimulationConfig

config = SimulationConfig(
    num_firms=10,
    ai_productivity_multiplier=2.0,
    ai_wage_ratio=0.3,
    human_task_floor=0.35,
    demand_growth_rate=0.04,
    simulation_periods=240
)
engine = SimulationEngine(config)
results = engine.run()

print(f"Final unemployment: {results['unemployment_rate'].iloc[-1]:.1%}")
print(f"Wage growth: {(results['avg_wage_human'].iloc[-1] / results['avg_wage_human'].iloc[0] - 1)*100:.0f}%")
```

## Economic Model

### Production Function (Firm)
- **Additive Production**: Y = A × (L_H + m × L_AI)
- Labor allocation via CES first-order condition with elasticity σ (default 1.5)
- **Human task floor**: minimum 40% of labor must be human (oversight, creativity, relationships)

### Labor Matching (Market)
- **Cobb-Douglas Matching**: M = A·U^α·V^(1-α)
- **Directed Search** (Moen 1997): application probability proportional to posted wage
- **On-the-Job Search**: employed workers sample outside offers (poaching)

### Wage Determination (Competitive MPL-Based)
- Firms post wages = MPL × labor_share × (1 + tightness_adjustment)
- Market wage emerges as employment-weighted average of firm postings
- AI augmentation raises human MPL → drives wage growth

### Demand & Pricing
- **Inverse Demand**: P = a × (1 - Q/Q_max), floor at 0.1
- **Growing Market Capacity**: Q_max grows at 3%/yr + endogenous response to utilization
- Prevents permanent demand deficiency (Say's Law)

### New Task Creation (Acemoglu-Restrepo)
- Human task floor starts at 40%, grows with AI adoption (0.2%/month)
- More AI → more need for human oversight, creative direction, ethical judgment
- Caps at 65% maximum

### Firm Exit
- On 6 consecutive months of losses (firms use capital reserves to survive downturns)

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

## Documentation

- **[docs/architecture.md](docs/architecture.md)**: System design, economic model, parameters, validation strategy
- **[docs/development-history.md](docs/development-history.md)**: Phase-by-phase implementation record
- **[docs/roadmap.md](docs/roadmap.md)**: Remaining work

## Key Design Features

✓ **Additive Production** - CES labor allocation with human task floor  
✓ **Cobb-Douglas Matching** - Micro-founded directed job search  
✓ **MPL-Based Wages** - Competitive wage posting with poaching  
✓ **Oligopolistic Firms** - Cournot-style output competition  
✓ **New Task Creation** - Acemoglu-Restrepo reinstatement mechanism  
✓ **Growing Demand** - Say's Law prevents permanent demand deficiency  
✓ **AI Augmentation** - Humans with AI tools are more productive  
✓ **Gradual Adoption** - Implementation friction (realistic S-curve diffusion)  
✓ **Policy Integration** - Wage subsidies, retraining, R&D credits affect outcomes  
✓ **Parsimony** - Monthly time-steps (240 periods = 20 years)  
✓ **Extensibility** - Clean agent/market/simulation separation  

## Dependencies

- `numpy` - Numerical computing
- `pandas` - Data analysis
- `pydantic` - Configuration validation
- `pytest` - Testing
- `matplotlib`, `plotly` - Visualization
- `scipy` - Scientific computing
- `streamlit` - Interactive dashboard

See `requirements.txt`.

## Next Steps

See [docs/roadmap.md](docs/roadmap.md) for remaining work:
- **Phase 7**: Enhanced visualization & interactive dashboards
- **Phase 8**: Sensitivity analysis, additional scenarios, publication-ready outputs

## License

Research use.
