"""Diagnostic: trace no-AI scenario to find remaining unemployment source."""
import numpy as np
from src.simulation.engine import SimulationEngine
from src.config.parameters import SimulationConfig
from src.agents.worker import WorkerStatus

config = SimulationConfig(
    num_firms=3,
    initial_human_workers=1000,
    simulation_periods=60,
    matching_efficiency=1.5,
    ai_productivity_multiplier=0.1,
    ai_wage_ratio=2.0,
    ai_initial_adoption_share=0.0,
    random_seed=42,
)
engine = SimulationEngine(config)

print(f'Config: a={config.output_price_intercept}, Q_max={config.output_market_capacity or 4*config.initial_human_workers}')
print(f'AI: mult={config.ai_productivity_multiplier}, cost={config.ai_wage_ratio}')
print()

header = f'{"Prd":>4} {"Wkrs":>5} {"Emp":>5} {"Unemp":>6} {"U%":>6} {"Vac":>5} {"Match":>5} {"AvgWage":>8} {"MktWage":>8}'
print(header)
for t in range(24):
    engine.step()
    m = engine.metrics.metrics_history[-1]
    print(f'{t:>4} {len(engine.workers):>5} {m.num_employed_human:>5} {m.num_unemployed:>6} '
          f'{m.unemployment_rate:>6.1%} {m.job_vacancies:>5} {m.job_matches:>5} '
          f'{m.avg_wage_human:>8.3f} {engine.market_wage_human:>8.3f}')

# Trace firm demand details
print('\n=== FIRM DEMAND DETAILS ===')
a = config.output_price_intercept
q_max = config.output_market_capacity or 4 * config.initial_human_workers
n_firms = len(engine.firms)
for fid, f in list(engine.firms.items())[:5]:
    prod = f.productivity_draw * f.state.human_productivity
    w = f.state.posted_wage_human
    mc = w / max(prod, 0.01)
    if a > mc:
        ot = q_max * (a - mc) / (a * (n_firms + 1))
    else:
        ot = 1
    h_d, ai_d = f.compute_labor_demand(w, f.state.posted_cost_ai, ot)
    net = max(0, h_d - f.state.human_workers_employed)
    print(f'  Firm {fid}: prod={prod:.2f} wage={w:.3f} MC={mc:.3f} '
          f'Cournot_q={ot:.0f} h_demand={h_d} current={f.state.human_workers_employed} '
          f'net_openings={net} ai_demand={ai_d}')

# Check reservation wages
unemp_workers = [(wid, w) for wid, w in engine.workers.items() if w.state.status == WorkerStatus.UNEMPLOYED]
if unemp_workers:
    res_wages = [w.state.reservation_wage for _, w in unemp_workers[:20]]
    print(f'\n=== RESERVATION WAGES (first 20 unemployed) ===')
    print(f'  Range: {min(res_wages):.3f} to {max(res_wages):.3f}')
    print(f'  Mean: {np.mean(res_wages):.3f}')
    print(f'  Market wage: {engine.market_wage_human:.3f}')
    
    # Check what wages firms are offering vs reservation wages
    firm_wages = [f.state.posted_wage_human for f in engine.firms.values()]
    print(f'  Firm wages: {[f"{w:.3f}" for w in firm_wages]}')
    print(f'  Would workers accept? {[res_wages[0] <= fw for fw in firm_wages]}')
