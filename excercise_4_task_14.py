import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pyomo.opt import SolverFactory
from pyomo.core import Var
import pyomo.environ as en
import time
from exercise_4_battery_vs_grid_investment import load_time_series_subset_aggr 

# Read battery specification 
parametersinput = pd.read_csv('./battery_data.csv', index_col=0)
parameters = parametersinput.loc[1]

# Battery Specification
capacity = 2
charging_power_limit = 1
discharging_power_limit = 1
charging_efficiency = parameters["Battery_Charge_Efficiency"]
discharging_efficiency = parameters["Battery_Discharge_Efficiency"]
P_lim=4    #new

# Read load and PV profile data
testData = pd.read_csv('./profile_input.csv')

# Convert the various timeseries/profiles to numpy arrays
base_load=load_time_series_subset_aggr*1.03**6
pv_production = np.zeros_like(base_load)
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
model.p_lim = en.Param(initialize = P_lim )

# Define variables
model.soc = en.Var(model.T, bounds=(0, capacity), initialize=0)  # State of charge
model.p_charge = en.Var(model.T, bounds=(0, charging_power_limit), initialize=0)  # Charging power
model.p_discharge = en.Var(model.T, bounds=(0, discharging_power_limit), initialize=0)  # Discharging power
model.from_grid = en.Var(model.T, initialize=0)  # Net load from the grid

# Objective function: Minimize the total electricity cost
def objective_rule(model):
    return sum(model.buy_price[t] * model.p_discharge[t] for t in model.T)
model.objective = en.Objective(rule=objective_rule, sense=en.maximize)

# Constraints
def energy_balance_rule(model, t):
    return model.from_grid[t] == model.base_load[t] - model.pv_production[t] + model.p_charge[t]  - model.p_discharge[t] 
model.energy_balance = en.Constraint(model.T, rule=energy_balance_rule)

def soc_dynamics_rule(model, t):
    if t == 0:
        return model.soc[t] == 0
    else:
        return model.soc[t] == model.soc[t-1] + model.charging_efficiency * model.p_charge[t-1] - model.p_discharge[t-1] / model.discharging_efficiency
model.soc_dynamics = en.Constraint(model.T, rule=soc_dynamics_rule)

#Added new constraint making sure that state of charge is always below the capacity
def soc_capacity_rule(model, t):
    return model.soc[t] <= model.capacity
model.soc_capacity = en.Constraint(model.T, rule=soc_capacity_rule)

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

#Ensure no discharge when SOC is zero
def dicharging_SOC_rule(model, t):
    return model.p_discharge[t] <= model.soc[t] * model.discharging_power_limit
model.dicharging_soc = en.Constraint(model.T, rule=dicharging_SOC_rule)

# New rule for Excercise 6

def powerLimit_rule(model, t):
    return model.from_grid[t] <= P_lim
model.powerLimit = en.Constraint(model.T, rule=powerLimit_rule)

# Solve the optimization problem
solver = SolverFactory('gurobi')
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
plt.figure(figsize=(8, 6))  # Adjusted the width to 8 and height to 6
plt.subplot(4, 1, 1)
plt.plot(hours, base_load, label='Base Load', color='blue')
plt.plot(hours, pv_production, label='PV Generation', color='orange')
plt.ylabel('Power (MW)')
plt.title('Base Load and PV Generation')
plt.legend()

plt.subplot(4, 1, 2)
plt.plot(hours, from_grid, label='From Grid')
plt.ylabel('Power (MW)')
plt.legend()

plt.subplot(4, 1, 3)
plt.plot(hours, soc, label='State of Charge (SOC)', color='green')
plt.ylabel('Energy (MWh)')
plt.legend()

plt.subplot(4, 1, 4)
plt.plot(hours, p_charge, label='Charging Power')
plt.plot(hours, p_discharge, label='Discharging Power')
plt.xlabel('Hour')
plt.ylabel('Power (MW)')
plt.legend()

plt.tight_layout()
plt.show()

##### task 3 #####
#Plotting charge/discharge power schedule for the battery
plt.figure(figsize=(8, 4))  # Adjusted the width to 8 and height to 4
plt.plot(hours, p_charge, label='Charging Power', color='blue')
plt.plot(hours, p_discharge, label='Discharging Power', color='red')
plt.xlabel('Hour')
plt.ylabel('Power (MW)')
plt.title('Charge/Discharge Power Schedule')
plt.legend()
plt.show()

#### end of task 3### 
# Plotting base load and power from grid in one plot to answer task 4
plt.figure(figsize=(8, 4))  # Adjusted the width to 8 and height to 4
plt.plot(hours, base_load, label='Base Load', color='blue')
plt.plot(hours, from_grid, label='From Grid', color='red')
plt.axhline(y=0, color='black', linestyle='--') 
plt.xlabel('Hour')
plt.ylabel('Power (MW)')
plt.legend()
plt.show()
### end of task 4


# Plotting base load, power from grid, and electricity price in one plot to answer task 5
fig, ax1 = plt.subplots(figsize=(8, 4))  # Adjusted the width to 8 and height to 4
ax1.plot(hours, base_load, label='Base Load', color='blue')
ax1.plot(hours, from_grid, label='From Grid', color='red')
ax1.axhline(y=0, color='black', linestyle='--')  # Add horizontal line at y = 0
ax1.set_xlabel('Hour')
ax1.set_ylabel('Power (MW)')
ax1.legend(loc='upper right')  # Move legend to the right

ax2 = ax1.twinx()
ax2.plot(hours, buy_price, label='Electricity Price', color='green')
ax2.set_ylabel('Price (NOK/kWh)')
ax2.legend(loc='center right')  # Move legend to the right

plt.title('Base Load, Power from Grid, and Electricity Price')
plt.tight_layout()
plt.show()

# Combined plot for charge/discharge power and state of charge
fig, ax1 = plt.subplots(figsize=(8, 4))
ax1.plot(hours, p_charge, label='Charging Power', color='blue')
ax1.plot(hours, p_discharge, label='Discharging Power', color='red')
ax1.plot(hours, soc, label='State of Charge (SOC)', color='green')
ax1.set_xlabel('Hour')
ax1.set_ylabel('Power (MW)')
ax1.legend(loc='upper right')


plt.title('Charge/Discharge Power and State of Charge')
plt.tight_layout()
plt.show()