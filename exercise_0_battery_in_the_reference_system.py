# -*- coding: utf-8 -*-
"""
Created on 2023-07-13

@author: ivespe

Intro script for warm-up exercise ("exercise 0") in specialization course module 
"Flexibility in power grid operation and planning" at NTNU (TET4565/TET4575) 
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
import math

# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
#path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'
#path_data_set = "/Users/ingridwiig/Documents/NTNU/5. klasse/Modul3/CINELDI_MV_reference_system_v_2023-03-06/"
#path_data_set = "/Users/andreamarie/Documents/Blokk 3 - fordypningsemne fleksibilitet /Oving 0/CINELDI_MV_reference_system_v_2023-03-06/"
path_data_set = "C:/Users/haral/CINELDI_MV_reference_system_v_2023-03-06/"

filename_residential_fullpath = os.path.join(path_data_set,'time_series_IDs_primarily_residential.csv')
filename_irregular_fullpath = os.path.join(path_data_set,'time_series_IDs_irregular.csv')      
filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')

# %% Read pandapower network
net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

#adding a load of 1MW at . positive values equals load
p_mw = 1
pf = 0.95
q_mvar = p_mw * math.tan(math.acos(pf))

pp.create_load(net, 95, p_mw, q_mvar, const_z_percent=0, const_i_percent=0)
# %% Test running power flow with a peak load model
# (i.e., all loads are assumed to be at their annual peak load simultaneously)

#insterting battery
#pp.create_load(net, 94, -p_mw*10, -q_mvar, const_z_percent=0, const_i_percent=0)

pp.runpp(net,init='results',algorithm='bfsw')

print('Total load demand in the system assuming a peak load model: ' + str(net.res_load['p_mw'].sum()) + ' MW')

# %% Plot results of power flow calculations

pp_plotting.pf_res_plotly(net)

# %%

