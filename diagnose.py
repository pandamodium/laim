"""Diagnostic: trace one period to confirm double-separation and headcount drift."""
import numpy as np
from src.simulation.engine import SimulationEngine
from src.config.parameters import SimulationConfig
from src.agents.worker import WorkerStatus

config = SimulationConfig(num_firms=3, initial_human_workers=100, random_seed=42)
engine = SimulationEngine(config)

print('=== INITIAL STATE ===')
emp_w = sum(1 for w in engine.workers.values() if w.state.status == WorkerStatus.EMPLOYED)
emp_f = sum(f.state.human_workers_employed for f in engine.firms.values())
print(f'  Employed (worker status): {emp_w}')
print(f'  Employed (firm counters): {emp_f}')
for fid, f in engine.firms.items():
    print(f'    Firm {fid}: {f.state.human_workers_employed} workers')

# --- Step 3: worker.step() separations ---
separated = 0
for w in engine.workers.values():
    old = w.state.status
    w.step(env=engine)
    if old == WorkerStatus.EMPLOYED and w.state.status == WorkerStatus.UNEMPLOYED:
        separated += 1

emp_w2 = sum(1 for w in engine.workers.values() if w.state.status == WorkerStatus.EMPLOYED)
emp_f2 = sum(f.state.human_workers_employed for f in engine.firms.values())
print(f'\n=== AFTER worker.step() ===')
print(f'  Workers separated (status change): {separated}')
print(f'  Employed (worker status): {emp_w2}')
print(f'  Employed (firm counters): {emp_f2}  <-- NOT decremented!')
print(f'  Headcount drift: {emp_f2 - emp_w2}')

# --- See what hire_workers would do ---
np.random.seed(99)
print(f'\n=== hire_workers() ALSO does binomial separation ===')
for fid, f in engine.firms.items():
    sep = int(np.random.binomial(f.state.human_workers_employed, config.separation_rate_employed))
    print(f'  Firm {fid} ({f.state.human_workers_employed} workers): would separate {sep} MORE')

# --- Check population growth ---
print(f'\n=== POPULATION GROWTH ===')
print(f'  human_population_growth_rate = {config.human_population_growth_rate}')
print(f'  Total workers at start: {len(engine.workers)}')
# Check if any code adds new workers
import inspect
source = inspect.getsource(engine.step)
has_pop_growth = 'population' in source or 'new_worker' in source or 'grow' in source
print(f'  Population growth in step()? {has_pop_growth}')

# --- Labor demand sanity check ---
print(f'\n=== LABOR DEMAND (first period) ===')
for fid, f in engine.firms.items():
    # This is what firms_post_jobs uses
    output_target = max(1, f.state.human_workers_employed) * f.state.human_productivity
    h_demand, ai_demand = f.compute_labor_demand(f.state.posted_wage_human, f.state.posted_cost_ai, output_target)
    net_openings = max(0, h_demand - f.state.human_workers_employed)
    print(f'  Firm {fid}: has={f.state.human_workers_employed}, output_target={output_target:.0f}, '
          f'h_demand={h_demand}, net_openings={net_openings}, ai_demand={ai_demand}')
