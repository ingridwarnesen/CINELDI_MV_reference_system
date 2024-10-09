import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pyomo.opt import SolverFactory
from pyomo.core import Var
import pyomo.environ as en
import time

# Read battery specification 
parametersinput = pd.read_csv('./battery_data.csv', index_col=0)
parameters = parametersinput.loc[1]

# Battery Specification
capacity = parameters['Battery_Capacity']
charging_power_limit = parameters["Battery_Power"]
discharging_power_limit = parameters["Battery_Power"]
charging_efficiency = parameters["Battery_Charge_Efficiency"]
discharging_efficiency = parameters["Battery_Discharge_Efficiency"]

# Read load and PV profile data
testData = pd.read_csv('./profile_input.csv')

# Convert the various timeseries/profiles to numpy arrays
base_load = testData['Base_Load'].values
pv_production = testData['PV'].values
sell_price = testData['Feed_Price'].values
buy_price = testData['Load_Price'].values

# Define the optimization model
model = en.ConcreteModel()

# Define sets
model.T = en.RangeSet(0, 23)  # 24 hours

# Define parameters
model.base_load = en.Param(model.T, initialize=dict(enumerate(base_load)))
model.pv_production = en.Param(model.T, initialize=dict(enumerate(pv_production)))
model.sell_price = en.Param(model.T, initialize=dict(enumerate(sell_price)))
model.buy_price = en.Param(model.T, initialize=dict(enumerate(buy_price)))
model.capacity = en.Param(initialize=capacity)
model.charging_power_limit = en.Param(initialize=charging_power_limit)
model.discharging_power_limit = en.Param(initialize=discharging_power_limit)
model.charging_efficiency = en.Param(initialize=charging_efficiency)
model.discharging_efficiency = en.Param(initialize=discharging_efficiency)

# Define variables
model.soc = en.Var(model.T, bounds=(0, capacity), initialize=0)  # State of charge
model.p_charge = en.Var(model.T, bounds=(0, charging_power_limit), initialize=0)  # Charging power
model.p_discharge = en.Var(model.T, bounds=(0, discharging_power_limit), initialize=0)  # Discharging power
model.from_grid = en.Var(model.T, initialize=0)  # Net load from the grid

# Objective function: Minimize the total electricity cost
def objective_rule(model):
    return sum(model.buy_price[t] * model.from_grid[t] for t in model.T)
model.objective = en.Objective(rule=objective_rule, sense=en.minimize)

# Constraints
def energy_balance_rule(model, t):
    return model.from_grid[t] == model.base_load[t] - model.pv_production[t] + model.p_charge[t]  - model.p_discharge[t] 
model.energy_balance = en.Constraint(model.T, rule=energy_balance_rule)

def soc_dynamics_rule(model, t):
    if t == 0:
        return model.soc[t] == 0
    else:
        return model.soc[t] == model.soc[t-1] + model.charging_efficiency * model.p_charge[t] - model.p_discharge[t] / model.discharging_efficiency
model.soc_dynamics = en.Constraint(model.T, rule=soc_dynamics_rule)

#state of charge is set to zero at
def final_soc_rule(model):
    return model.soc[23] == 0
model.final_soc = en.Constraint(rule=final_soc_rule)

# Ensure p_charge at time 0 is zero
def p_charge_initial_rule(model):
    return model.p_charge[0] == 0
model.p_charge_initial = en.Constraint(rule=p_charge_initial_rule)

# Ensure p_discharge at time 0 is zero
def p_discharge_initial_rule(model):
    return model.p_discharge[0] == 0
model.p_discharge_initial = en.Constraint(rule=p_discharge_initial_rule)

# Solve the optimization problem
solver = SolverFactory('glpk')
results = solver.solve(model, tee=True)

# Print results
print("Objective value: ", en.value(model.objective))
for t in model.T:
    print(f"Hour {t}: From Grid = {en.value(model.from_grid[t]):.2f}, SOC = {en.value(model.soc[t]):.2f}, Charge = {en.value(model.p_charge[t]):.2f}, Discharge = {en.value(model.p_discharge[t]):.2f}")

# Plot results
hours = range(24)
from_grid = [en.value(model.from_grid[t]) for t in model.T]
soc = [en.value(model.soc[t]) for t in model.T]
p_charge = [en.value(model.p_charge[t]) for t in model.T]
p_discharge = [en.value(model.p_discharge[t]) for t in model.T]

# Combined plot for base load and PV generation
plt.subplot(4, 1, 1)
plt.plot(hours, base_load, label='Base Load', color='blue')
plt.plot(hours, pv_production, label='PV Generation', color='orange')
plt.ylabel('Power (kW)')
plt.title('Base Load and PV Generation')
plt.legend()

plt.subplot(4, 1, 2)
plt.plot(hours, from_grid, label='From Grid')
plt.ylabel('Power (kW)')
plt.legend()

plt.subplot(4, 1, 3)
plt.plot(hours, soc, label='State of Charge (SOC)')
plt.ylabel('Energy (kWh)')
plt.legend()

plt.subplot(4, 1, 4)
plt.plot(hours, p_charge, label='Charging Power')
plt.plot(hours, p_discharge, label='Discharging Power')
plt.xlabel('Hour')
plt.ylabel('Power (kW)')
plt.legend()

plt.tight_layout()
plt.show()