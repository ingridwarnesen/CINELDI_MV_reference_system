# -*- coding: utf-8 -*-
"""
Created on 2023-10-10

@author: ivespe

Intro script for Exercise 4 ("Battery energy storage system in the grid vs. grid investments") 
in specialization course module "Flexibility in power grid operation and planning" 
at NTNU (TET4565/TET4575) 

"""


# %% Dependencies

import pandas as pd
import os
import load_profiles as lp
import pandapower_read_csv as ppcsv
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
#path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'
#path_data_set = "/Users/ingridwiig/Documents/NTNU/5. klasse/Modul3/CINELDI_MV_reference_system_v_2023-03-06/"
path_data_set = "C:/Users/haral/CINELDI_MV_reference_system_v_2023-03-06/"


filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')
filename_standard_overhead_lines = os.path.join(path_data_set,'standard_overhead_line_types.csv')
filename_reldata = os.path.join(path_data_set,'reldata_for_component_types.csv')
filename_load_point = os.path.join(path_data_set,'CINELDI_MV_reference_system_load_point.csv')

# Subset of load buses to consider in the grid area, considering the area at the end of the main radial in the grid
bus_i_subset = [90, 91, 92, 96]

# Assumed power flow limit in MW that limit the load demand in the grid area (through line 85-86)
P_lim = 4

# Factor to scale the loads for this exercise compared with the base version of the CINELDI reference system data set
scaling_factor = 10

# Read standard data for overhead lines
data_standard_overhead_lines = pd.read_csv(filename_standard_overhead_lines, delimiter=';')
data_standard_overhead_lines.set_index(keys = 'type', drop = True, inplace = True)

# Read standard component reliability data
data_comp_rel = pd.read_csv(filename_reldata, delimiter=';')
data_comp_rel.set_index(keys = 'main_type', drop = True, inplace = True)

# Read load point data (incl. specific rates of costs of energy not supplied) for data
data_load_point = pd.read_csv(filename_load_point, delimiter=';')
data_load_point.set_index(keys = 'bus_i', drop = True, inplace = True)


# %% Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)


# %% Set up hourly normalized load time series for a representative day (task 2; this code is provided to the students)

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Consider only the day with the peak load in the area (28 February)
repr_days = [31+28]

# Get relative load profiles for representative days mapped to buses of the CINELDI test network;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,repr_days)

# Calculate load time series in units MW (or, equivalently, MWh/h) by scaling the normalized load time series by the
# maximum load value for each of the load points in the grid data set (in units MW); the column index is the bus number
# (1-indexed) and the row index is the hour of the year (0-indexed)
load_time_series_mapped = profiles_mapped.mul(net.load['p_mw'])

# %% Aggregate the load demand in the area

# Aggregated load time series for the subset of load buses
load_time_series_subset = load_time_series_mapped[bus_i_subset] * scaling_factor
load_time_series_subset_aggr = load_time_series_subset.sum(axis=1)
P_max = load_time_series_subset_aggr.max()

##### begin task 2 #####


# Calculate peak load demand for each year over the 10-year planning horizon
years = np.arange(0, 11)
peak_loads = [P_max * (1 + 0.03) ** year for year in years]

# Plot the peak load demand over the planning horizon
plt.figure(figsize=(10, 6))
plt.plot(years, peak_loads, marker='o', label='Annual peak load demand')
plt.axhline(y=P_lim, color='r', linestyle='--', label='Power flow limit (P_lim)')
plt.xlabel('Year')
plt.ylabel('Peak load demand (MW)')
plt.title('Peak load demand over the 10 year horizon with 3% annual growth')
plt.legend()
plt.grid(True)
plt.show()

### end task 2 ###


#Task 3
data_standard_overhead_lines = pd.read_csv(filename_standard_overhead_lines, delimiter=';')
print(data_standard_overhead_lines.columns)

type_new_line = '111-AL1/19-ST1A (FeAl nr. 70 6/1) '

cost_per_km_new_line = data_standard_overhead_lines.loc[data_standard_overhead_lines['type'] == type_new_line, 'cost_NOK_per_km'].values[0]

#Length of line 85-86 (main feeder)
length_MF = 20
investment_cost_new_line = cost_per_km_new_line * length_MF
print(investment_cost_new_line)

###Task7###
loadasList=load_time_series_subset_aggr.copy()
loadYears=[]
loadYears.append(loadasList.values.tolist())   #Load time series of the worst day for the fisrt year
for i in years[1:]:
    loadasList=loadasList*1.03                           #Adding the load time series for the next ten years with expected increase on demand
    loadYears.append(loadasList.values.tolist())
flexibilityCost=[]
priceOfFlex=2000
for yearlist in loadYears[:-1]:                            #The battery only has to operate the first nine years (until grid capacity is expanded)
    flexYear=0
    for i in range(len(yearlist)):
        if(yearlist[i]>P_lim):
            flexYear+=(yearlist[i]-P_lim)*priceOfFlex           #Price of using the battery times the amount needed during each hour
    flexibilityCost.append(flexYear*20)                #for 20 days of the year

print(flexibilityCost)
#making list of load values
###Endof Task 7 ###
###Task  9###
#Found average interuption cost to be 2.4 hrs, which is closer to 1h than 4h.
#Using this for all years
#avg_interuptionCost
filtered_data_load_point = data_load_point.loc[bus_i_subset]
total_c_NOK_per_kWh_1h = filtered_data_load_point['c_NOK_per_kWh_1h'].sum()
print("Total c_NOK_per_kWh_1h for specified buses:", total_c_NOK_per_kWh_1h)


###Task 14###
