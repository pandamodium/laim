"""Diagnostic: trace full pipeline with fixes applied."""
import numpy as np
from src.simulation.engine import SimulationEngine
from src.config.parameters import SimulationConfig
from src.agents.worker import WorkerStatus

config = SimulationConfig(num_firms=3, initial_human_workers=100, random_seed=42)
engine = SimulationEngine(config)

# Run 24 periods and track
print(f'{"Period":>6} {"Workers":>8} {"Emp(w)":>7} {"Emp(f)":>7} {"Unemp":>6} {"Drift":>6} {"Vacancies":>10} {"Matches":>8}')
for t in range(24):
    emp_w = sum(1 for w in engine.workers.values() if w.state.status == WorkerStatus.EMPLOYED)
    emp_f = sum(f.state.human_workers_employed for f in engine.firms.values())
    unemp = sum(1 for w in engine.workers.values() if w.state.status == WorkerStatus.UNEMPLOYED)
    total = len(engine.workers)
    
    engine.step()
    
    # Get metrics from the last recorded period
    last_metrics = engine.metrics.metrics_history[-1] if engine.metrics.metrics_history else None
    vac = last_metrics.job_vacancies if last_metrics else 0
    matches = last_metrics.job_matches if last_metrics else 0
    
    emp_w2 = sum(1 for w in engine.workers.values() if w.state.status == WorkerStatus.EMPLOYED)
    emp_f2 = sum(f.state.human_workers_employed for f in engine.firms.values())
    
    print(f'{t:>6} {total:>8} {emp_w2:>7} {emp_f2:>7} {unemp:>6} {emp_f2-emp_w2:>6} {vac:>10} {matches:>8}')

# Final check
print(f'\nFinal: {len(engine.workers)} workers, {len(engine.firms)} firms')
print(f'Final unemployment rate: {engine.unemployment_rate:.1%}')

# Check Cournot output targets
print(f'\n=== FIRM LABOR DEMAND (Cournot) ===')
a = config.output_price_intercept
q_max = config.output_market_capacity or 4.0 * config.initial_human_workers
n_firms = len(engine.firms)
for fid, f in list(engine.firms.items())[:5]:
    prod = f.productivity_draw * f.state.human_productivity
    mc = f.state.posted_wage_human / max(prod, 0.01)
    if a > mc:
        output_target = q_max * (a - mc) / (a * (n_firms + 1))
    else:
        output_target = 1.0
    h_demand, ai_demand = f.compute_labor_demand(f.state.posted_wage_human, f.state.posted_cost_ai, output_target)
    print(f'  Firm {fid}: prod_draw={f.productivity_draw:.2f} wage={f.state.posted_wage_human:.3f} '
          f'MC={mc:.3f} output_target={output_target:.0f} h_demand={h_demand} ai_demand={ai_demand} '
          f'current_emp={f.state.human_workers_employed}')
