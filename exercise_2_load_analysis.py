# -*- coding: utf-8 -*-
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
#path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'
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



# Retrieve load time series for new load to be added to the area
new_load_profiles = load_profiles.get_profile_days(repr_days)
new_load_time_series = new_load_profiles[i_time_series_new_load]*P_max_new

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
