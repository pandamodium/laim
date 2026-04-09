"""Diagnostic: trace firm profits to find exit trigger."""
import numpy as np
from src.simulation.engine import SimulationEngine
from src.config.parameters import SimulationConfig
from src.agents.worker import WorkerStatus

config = SimulationConfig(
    num_firms=3, initial_human_workers=1000,
    ai_productivity_multiplier=0.1, ai_wage_ratio=2.0,
    ai_initial_adoption_share=0.0, random_seed=42,
)
engine = SimulationEngine(config)

print(f'{"Prd":>4} {"Price":>6} {"TotOut":>7} | ', end='')
for fid in range(3):
    print(f'F{fid}:emp/out/rev/cost/profit  | ', end='')
print()

for t in range(15):
    engine.step()
    m = engine.metrics.metrics_history[-1]
    price = engine._compute_output_price()
    
    print(f'{t:>4} {price:>6.3f} {engine.total_output:>7.0f} | ', end='')
    for fid in sorted(engine.firms.keys())[:3]:
        f = engine.firms[fid]
        rev = price * f.state.output_produced
        cost = (f.state.posted_wage_human * f.state.human_workers_employed +
                f.state.posted_cost_ai * f.state.ai_workers_employed)
        print(f'  {f.state.human_workers_employed:>4}/{f.state.output_produced:>6.0f}/{rev:>7.0f}/{cost:>7.0f}/{f.state.profits:>+7.0f} | ', end='')
    
    if len(engine.firms) < 3:
        print(f'  [ONLY {len(engine.firms)} FIRMS LEFT]', end='')
    print()
    
    if len(engine.firms) == 0:
        print('  ALL FIRMS EXITED!')
        break
