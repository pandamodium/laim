# AI Labor Market Simulation

An agentic framework for analyzing the macroeconomic impact of AI on labor markets through agent-based modeling. The simulation examines how oligopolistic firms, human workers, and AI agents interact in a dynamic labor market with endogenous business formation.

**Status**: ✅ Phase 2 Complete - Full Simulation Engine Operational (40/40 tests passing)

## Features

- **Multi-Agent System**: Firms and workers with individual economic decision-making
- **Oligopolistic Competition**: 3 firms (configurable) with dynamic pricing
- **Labor Market Matching**: Micro-founded job search with Cobb-Douglas matching function
- **Wage Dynamics**: Phillips curve adjustment responding to unemployment and AI share
- **Comprehensive Metrics**: Track hiring, unemployment, job openings, wages, firm dynamics
- **Extensible Framework**: Ready for business formation, heterogeneity, policy analysis

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
│   ├── agents/           
│   │   ├── firm.py       [✓ CES production, profit, R&D]
│   │   ├── worker.py     [✓ Job search, entrepreneurship]
│   │   └── ai_agent.py   [✓ Pooled AI tracking]
│   ├── market/           
│   │   ├── job_market.py [✓ Job posting & matching]
│   │   ├── matching.py   [✓ Cobb-Douglas matching]
│   │   └── wage_dynamics.py [✓ Phillips curve]
│   ├── simulation/
│   │   └── engine.py     [✓ Full orchestration, 12-step cycle]
│   ├── analytics/
│   │   ├── metrics.py    [✓ Results tracking]
│   │   └── visualization.py [In progress]
│   └── config/
│       └── parameters.py [✓ 50+ validated parameters]
├── tests/                [✓ 40/40 passing (Phase 1+2)]
├── outputs/              # Results, visualizations
├── PHASE1_SUMMARY.md     # Core agents complete
├── PHASE2_SUMMARY.md     # Market mechanics complete
├── IMPLEMENTATION_PLAN.md # 50-page architecture reference
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

### Phase 3: Enhancements (In Design)
- Entrepreneurial business formation pipeline
- Oligopolistic pricing (Cournot competition)
- Population dynamics (labor supply growth)
- Sectoral heterogeneity

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

# With coverage
pytest tests/ --cov=src --cov-report=html
```

**Status**: 40/40 tests passing ✅
- Phase 1: 25 tests (agents, configuration, basic market)
- Phase 2: 15 tests (job market, simulation engine, dynamics)

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

## Documentation

- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** (50 pages): 
  - Full architecture with 10 potential issues + solutions
  - Parameter baseline with economic justification
  - Implementation sequence
  - Validation & calibration strategy

- **[PHASE1_SUMMARY.md](PHASE1_SUMMARY.md)**: Agent implementation details

- **[PHASE2_SUMMARY.md](PHASE2_SUMMARY.md)**: Market mechanics and engine

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

To continue development:

1. **Phase 3A**: Run exploratory simulations (baseline parameters)
2. **Phase 3B**: Implement business formation mechanics
3. **Phase 4**: Add heterogenous productivity and oligopoly refinements
4. **Phase 5**: Visualization dashboards
5. **Phase 6-8**: Calibration, validation, advanced analytics

## License

Research use.
