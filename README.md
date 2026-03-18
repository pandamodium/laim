# AI Labor Market Simulation

An agentic framework for analyzing the macroeconomic impact of AI on labor markets through agent-based modeling. The simulation examines how oligopolistic firms, human workers, and AI agents interact in a dynamic labor market with endogenous business formation.

## Features

- **Multi-Agent System**: Firms, workers, and AI agents with individual decision-making logic
- **Oligopolistic Competition**: Default 3 firms competing in output markets
- **Labor Market Matching**: Endogenous matching between firms and workers
- **Business Formation Dynamics**: Entrepreneurial entry driven by animal spirits and accumulated capital
- **R&D Investment**: Firms investing in innovation to improve productivity and reduce AI costs
- **Comprehensive Metrics**: Track hiring, unemployment, job openings, wages, and firm dynamics
- **Visualization**: Real-time dashboards and historical analysis

## Project Structure

```
ai_labor_market/
├── src/
│   ├── agents/           # Agent definitions (Firm, Worker, AIAgent)
│   ├── market/           # Matching function and market clearing
│   ├── simulation/       # Main simulation engine and step logic
│   ├── analytics/        # Metrics collection and analysis
│   ├── config/           # Configuration and parameters
│   └── __init__.py
├── tests/                # Unit and integration tests
├── outputs/              # Results, logs, visualizations
├── requirements.txt      # Python dependencies
└── README.md
```

## Getting Started

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Configuration is managed through `src/config/parameters.py`. Key parameters:

- `NUM_FIRMS`: Number of oligopolistic firms (default: 3)
- `INITIAL_WORKERS`: Initial human labor supply (default: 1000)
- `WORKER_GROWTH_RATE`: Annual human population growth (default: 0.02)
- `AI_PRODUCTIVITY_MULTIPLIER`: Productivity ratio (AI/human, default: 1.5)
- `AI_COST_RATIO`: Cost ratio (AI/human wage, default: 0.5)
- `ENTREPRENEURSHIP_RATE`: Annual business formation rate (default: 0.05)
- `SIMULATION_PERIODS`: Number of periods to simulate (default: 240 for 20 years)

## Running Simulations

```python
from src.simulation.engine import SimulationEngine
from src.config.parameters import SimulationConfig

config = SimulationConfig()
engine = SimulationEngine(config)
results = engine.run()
```

## Implementation Status

- [ ] Core agent classes
- [ ] Market matching function
- [ ] Firm production and hiring
- [ ] Worker supply and job search
- [ ] Business formation mechanics
- [ ] R&D and productivity dynamics
- [ ] Metrics tracking system
- [ ] Visualization layer
- [ ] Integration tests
- [ ] Documentation and examples

## Design Considerations

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed architecture, potential issues, and design decisions.

## License

This project is for research purposes.
