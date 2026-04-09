"""Relative impact analysis vs No-AI baseline."""
import pandas as pd
import numpy as np

base = pd.read_csv('outputs/scenario_analysis/1_No_AI_results.csv')
scenarios = ['2_Moderate_AI','3_Aggressive_AI','4_AI_as_Complement','5_Aggressive_AI_Policy','6_Superstar_Economy']

print('=== RELATIVE IMPACT vs NO-AI BASELINE (Year 20 averages) ===')
header = f'{"Scenario":<30} {"dUnemp(pp)":>12} {"dWage(%)":>12} {"dOutput(%)":>12} {"dHumanEmp":>12} {"AI/Human":>10}'
print(header)
print('-'*86)

base_yr20 = base.iloc[-12:]
b_u = base_yr20['unemployment_rate'].mean()
b_w = base_yr20['avg_wage_human'].mean()
b_o = base_yr20['total_output'].mean()
b_h = base_yr20['num_employed_human'].mean()

for sc in scenarios:
    df = pd.read_csv(f'outputs/scenario_analysis/{sc}_results.csv')
    yr20 = df.iloc[-12:]
    u = yr20['unemployment_rate'].mean()
    w = yr20['avg_wage_human'].mean()
    o = yr20['total_output'].mean()
    h = yr20['num_employed_human'].mean()
    ai = yr20['num_employed_ai'].mean()
    
    du = (u - b_u)*100
    dw = (w/b_w - 1)*100 if b_w > 0 else 0
    do_ = (o/b_o - 1)*100 if b_o > 0 else 0
    dh = h - b_h
    ratio = ai/h if h > 0 else float('inf')
    
    print(f'{sc:<30} {du:>+12.1f} {dw:>+12.1f} {do_:>+12.1f} {dh:>+12.0f} {ratio:>10.1f}')

# Wage volatility
print('\n=== WAGE VOLATILITY (Std of monthly avg wage) ===')
for sc in ['1_No_AI'] + scenarios:
    df = pd.read_csv(f'outputs/scenario_analysis/{sc}_results.csv')
    w_std = df['avg_wage_human'].std()
    w_cv = w_std / df['avg_wage_human'].mean() * 100
    print(f'  {sc:<30} Std={w_std:.3f}  CV={w_cv:.1f}%')

# Labor share of output
print('\n=== LABOR SHARE OF OUTPUT (Year 20) ===')
for sc in ['1_No_AI'] + scenarios:
    df = pd.read_csv(f'outputs/scenario_analysis/{sc}_results.csv')
    yr20 = df.iloc[-12:]
    w = yr20['avg_wage_human'].mean()
    h = yr20['num_employed_human'].mean()
    o = yr20['total_output'].mean()
    labor_share = (w * h) / o * 100 if o > 0 else 0
    profit = yr20['total_profit'].mean()
    profit_share = profit / o * 100 if o > 0 else 0
    print(f'  {sc:<30} LaborShare={labor_share:5.1f}%  ProfitShare={profit_share:5.1f}%')
