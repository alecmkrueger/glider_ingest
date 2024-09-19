'''
Module containing utilities for the package
'''
# Import Packages
import numpy as np
import xarray as xr
import datetime
from .Gridder import Gridder

# Define functions and classes
def print_time(message):
    '''Add the current time to the end of a message'''
    # Get current time
    current_time = datetime.datetime.today().strftime('%H:%M:%S')
    # Add time to message
    whole_message = f'{message}: {current_time}'
    # Print out the message
    print(whole_message)

def find_nth(haystack: str, needle: str, n: int) -> int:
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

def invert_dict(dict:dict) -> dict:
    return {value:key for key,value in dict.items()}

def add_gridded_data(ds_mission:xr.Dataset) -> xr.Dataset:
    '''Create gridder object and create the gridded dataset'''
    print_time('Adding Gridded Data')
    gridder = Gridder(ds_mission=ds_mission)
    gridder.create_gridded_dataset()
    ds_mission.update(gridder.ds_gridded)
    print_time('Finished Adding Gridded Data')
    return ds_mission

def get_polygon_coords(ds_mission:xr.Dataset) -> str:
    '''Get the polygon coords for the dataset global attributes'''
    lat_max = np.nanmax(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)
    lat_min = np.nanmin(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)
    lon_max = np.nanmax(ds_mission.longitude.values)
    lon_min = np.nanmin(ds_mission.longitude.values)
    polygon_1 = str(lat_max)+' '+str(ds_mission.longitude[np.where(ds_mission.latitude==lat_max)[0][0]].values) # northmost
    polygon_2 = str(ds_mission.latitude[np.where(ds_mission.longitude==lon_max)[0][0]].values)+' '+str(lon_max) # eastmost
    polygon_3 = str(lat_min)+' '+str(ds_mission.longitude[np.where(ds_mission.latitude==lat_min)[0][0]].values) # southmost
    polygon_4 = str(ds_mission.latitude[np.where(ds_mission.longitude==lon_min)[0][0]].values)+' '+str(lon_min) # westmost
    polygon_5 = polygon_1
    return 'POLYGON (('+polygon_1+' '+polygon_2+' '+polygon_3+' '+polygon_4+' '+polygon_5+'))'
