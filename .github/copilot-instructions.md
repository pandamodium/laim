<!-- Copilot-specific instructions for AI Labor Market Simulation project -->

## Project Context
This is an agent-based model (ABM) for analyzing the macroeconomic impact of AI on labor markets. It simulates oligopolistic firms (default 3), human workers (default 1000 with slow growth), AI agents (unlimited but with different productivity/cost), endogenous business formation, and R&D-driven productivity improvements.

## Architecture Overview
- **Agents**: Firm, Worker, AIAgentPool (simplified)
- **Market**: Matching function (Cobb-Douglas), wage dynamics (Phillips curve)
- **Simulation**: Monte Carlo dynamics with monthly time-steps
- **Analytics**: Metrics collection, visualization, sensitivity analysis

## Key Implementation Notes
1. **No individual AI agents**: AI agents are pooled by firm to reduce computational burden
2. **Static optimization**: Firms maximize current-period profits (no forward-looking behavior)
3. **Simple worker model**: Workers apply to jobs, accept if wage > reservation wage
4. **Monthly periods**: 240 periods = 20 years
5. **Entry/Exit**: Exogenous entrepreneurship rate + loss-based firm exit

## Configuration
All parameters in `src/config/parameters.py` (Pydantic-validated). Key defaults:
- `num_firms=3`
- `initial_human_workers=1000`
- `ai_productivity_multiplier=1.5`
- `ai_wage_ratio=0.5`
- `base_entrepreneurship_rate=0.05`

## Development Status
- [x] Project structure created
- [x] Configuration framework with validation
- [x] Agent base classes and stubs
- [x] Market mechanics stubs
- [x] Metrics collection framework
- [ ] Implement core agent behavior (Phase 1-2)
- [ ] Implement production and dynamics (Phase 3)
- [ ] Implement business formation (Phase 4)
- [ ] Implement R&D mechanics (Phase 5)
- [ ] Complete analytics and visualization (Phase 6-7)
- [ ] Integration testing and validation (Phase 8)

## Running the Simulation
```python
from src.simulation import SimulationEngine
from src.config import SimulationConfig

config = SimulationConfig()  # Or: create_custom_config(num_firms=5)
engine = SimulationEngine(config)
results = engine.run()
```

## Testing
Unit tests in `tests/` directory:
```bash
pytest tests/
```

## References
- See `IMPLEMENTATION_PLAN.md` for detailed architecture and design decisions
- See `README.md` for quick reference and feature overview
