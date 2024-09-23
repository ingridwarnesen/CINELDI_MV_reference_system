"""
Created on 2023-07-14

@author: ivespe

Intro script for Exercise 2 ("Load analysis to evaluate the need for flexibility") 
in specialization course module "Flexibility in power grid operation and planning" 
at NTNU (TET4565/TET4575) 

"""

# %% Dependencies

import pandapower as pp
import pandapower.plotting as pp_plotting
import pandas as pd
import os
import load_scenarios as ls
import load_profiles as lp
import pandapower_read_csv as ppcsv
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
#path_data_set         = '/Users/andreamarie/Documents/Blokk 3 - fordypningsemne fleksibilitet /Oving 0/CINELDI_MV_reference_system_v_2023-03-06/'
path_data_set = "C:/Users/haral/CINELDI_MV_reference_system_v_2023-03-06/"

filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')

# Subset of load buses to consider in the grid area, considering the area at the end of the main radial in the grid
bus_i_subset = [90, 91, 92, 96]

# Assumed power flow limit in MW that limit the load demand in the grid area (through line 85-86)
P_lim = 0.637 

# Maximum load demand of new load being added to the system
P_max_new = 0.4

# Which time series from the load data set that should represent the new load
i_time_series_new_load = 90


# %% Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

###################TASK2###################
def getLowestVoltage(loadDict, net):
    voltageList = []
    for key in loadDict:
        if key in net.bus['name'].values:
            voltage = net.res_bus.loc[key, 'vm_pu']
            voltageList.append(voltage)
    print(f'Lowest voltage in the area is {min(voltageList)} pu')
    return min(voltageList)


def LoadTable(loadDict):
    agg=0
    iteration=0
    print("Bus      Value")
    for key,value in loadDict.items():
        print(f"{key}      {value[0]}\n")
        agg+=value[0]
        iteration+=1
    print(f"Aggregated    {agg}\n")
    return(agg)

def multiplyBuses(buslist, scalingfactors):
    vList=[]
    aggList=[]
    for scfact in scalingfactors:
        net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)
        net.load.loc[net.load['bus'].isin(buslist), 'p_mw']*=scfact 
        pp.runpp(net,init='results',algorithm='bfsw')
        newloadDict={90:net.load.loc[net.load['bus']==90, 'p_mw'].values, 91:net.load.loc[net.load['bus']==91, 
            'p_mw'].values, 92:net.load.loc[net.load['bus']==92, 'p_mw'].values, 96:net.load.loc[net.load['bus']==96, 'p_mw'].values}
        aggList.append(LoadTable(newloadDict))
        vList.append(getLowestVoltage(newloadDict, net))

    plt.plot(aggList, vList, marker='o', linestyle='-', color='b')
    plt.xlabel('Aggregated Load (MW)')
    plt.ylabel('Voltage (p.u.)')
    plt.title('Voltage as a Function of Aggregated Load')
    plt.grid(True)
    plt.show()
scalingFactors=[1,1.2,1.4,1.6,1.8,2]
multiplyBuses(bus_i_subset, scalingFactors)
###################END OF TASK 2###############


# %% Set up hourly normalized load time series for a representative day (task 2; this code is provided to the students)

load_profiles = lp.load_profiles(filename_load_data_fullpath)



# Get all the days of the year
repr_days = list(range(1,366))

# Get relative load profiles for representative days mapped to buses of the CINELDI test network;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,repr_days)





# Retrieve load time series for new load to be added to the area. this load profile is given from the costumer requesting 0.4 MW
new_load_profiles = load_profiles.get_profile_days(repr_days)
new_load_time_series = new_load_profiles[i_time_series_new_load]*P_max_new #Scales the load profile for the new load by its maximum load demand

# Calculate load time series in units MW (or, equivalently, MWh/h) by scaling the normalized load time series by the
# maximum load value for each of the load points in the grid data set (in units MW); the column index is the bus number
# (1-indexed) and the row index is the hour of the year (0-indexed)
load_time_series_mapped = profiles_mapped.mul(net.load['p_mw'])
# %%

#Copied code from excercise 0 to use for task 1 excercise 2
pp.runpp(net,init='results',algorithm='bfsw')
print('Total load demand in the system assuming a peak load model: ' + str(net.res_load['p_mw'].sum()) + ' MW')
# %% Plot results of power flow calculations
pp_plotting.pf_res_plotly(net)

# Task 3
# Extracting dataframe containing bus 90, 91, 92, 96
load_dataframe_subset = load_time_series_mapped[bus_i_subset]
# Calculating aggregated values along axis = 1 (row values)
aggregated_values = load_dataframe_subset.sum(axis=1)

plt.plot(aggregated_values, label = "Aggregated load")
plt.axhline(y=P_lim, color='green', linestyle='--', label='Power flow limit (0.637 MW)')
plt.xlabel("Hour")
plt.ylabel("Load demand (MW)")
plt.title("Aggregated load demand for bus 90, 91, 92 and 96")
plt.legend()
plt.show()

pp.runpp(net,init='results',algorithm='bfsw')
pp_plotting.pf_res_plotly(net)
##task 8 plot --------
# Add new load to the existing load time series
load_time_series_with_new_load = load_time_series_mapped.copy()
load_time_series_with_new_load[bus_i_subset[0]] += new_load_time_series #her legges den nye load times serien (0.4 MW) med forbruksdate til bus 90 

# Calculate the aggregated load demand for the area
aggregated_load_demand_with_new_load = load_time_series_with_new_load[bus_i_subset].sum(axis=1)

# Calculate the load duration curve
load_duration_curve = aggregated_load_demand_with_new_load.sort_values(ascending=False).reset_index(drop=True)

# Find the intersection point
#intersection_index = (load_duration_curve > P_lim).sum()

# Plot the load duration curve
plt.figure(figsize=(12, 6))
plt.plot(load_duration_curve, label='Load Duration Curve')
plt.axhline(y=0.637, color='g', linestyle='--', label='Power Capacity (0.637 MW)')
#plt.scatter(intersection_index, P_lim, color='r', zorder=5)
#plt.text(intersection_index, 0, f'{intersection_index} hours', color='r', ha='center', va='bottom')
#plt.axvline(x=intersection_index, color='g', linestyle='--', label=f'Intersection at {intersection_index} hours')
plt.xlabel('Hours')
plt.ylabel('Load Demand (MW)')
plt.title('Load Duration Curve for Grid Area (bus 90, 91, 92, 96) with additional load time series added to bus 90')
plt.legend()
plt.grid(True)
plt.show()

### task 8 plot end--------------

# # pp.runpp(net,init='results',algorithm='bfsw')
# # #code for plotting
# # pp_plotting.pf_res_plotly(net)

### Task 13 ###
pp.runpp(net,init='results',algorithm='bfsw')
timeseries_constantmax=[0.4]*8760
load_time_series_with_newConstant_load = load_time_series_mapped.copy()
load_time_series_with_newConstant_load[bus_i_subset[0]] += timeseries_constantmax

# Calculate the aggregated load demand for the area
aggregated_load_demand_with_newConstant_load = load_time_series_with_newConstant_load[bus_i_subset].sum(axis=1)

# Calculate the load duration curve
load_duration_curve = aggregated_load_demand_with_newConstant_load.sort_values(ascending=False).reset_index(drop=True)

# Find the intersection point
#intersection_index = (load_duration_curve > P_lim).sum()

# Plot the load duration curve
plt.figure(figsize=(12, 6))
plt.plot(load_duration_curve, label='Load Duration Curve')
plt.axhline(y=0.637, color='g', linestyle='--', label='Power Capacity (0.637 MW)')
#plt.scatter(intersection_index, P_lim, color='r', zorder=5)
#plt.text(intersection_index, 0, f'{intersection_index} hours', color='r', ha='center', va='bottom')
#plt.axvline(x=intersection_index, color='g', linestyle='--', label=f'Intersection at {intersection_index} hours')
plt.xlabel('Hours')
plt.ylabel('Load Demand (MW)')
plt.title('Load Duration Curve for Grid Area (bus 90, 91, 92, 96) with constant load time series (0.4MW) added to bus 90')
plt.legend()
plt.grid(True)
plt.show()