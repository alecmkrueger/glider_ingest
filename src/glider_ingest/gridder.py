from attrs import define,field
import numpy as np
import pandas as pd
import xarray as xr


@define
class Gridder:
    '''
    Object to create and calculate the gridded dataset
    This object handles some functions that are coupled and to make the code easier to read
    '''
    ds_mission:xr.Dataset
    interval_h:int|float = field(default=1)
    interval_p:int|float = field(default=0.1)

    ds:xr.Dataset = field(init=False)
    ds_gridded:xr.Dataset = field(init=False)
    variable_names:list = field(init=False)
    time:np.ndarray = field(init=False)
    pres:np.ndarray = field(init=False)
    lat:np.ndarray = field(init=False)
    lon:np.ndarray = field(init=False)
    xx:np.ndarray = field(init=False)
    yy:np.ndarray = field(init=False)
    int_time:np.ndarray = field(init=False)
    int_pres:np.ndarray = field(init=False)
    data_arrays:dict = field(init=False)
    grid_pres:np.ndarray = field(init=False)
    grid_time:np.ndarray = field(init=False)

    def __attrs_post_init__(self):
        self.ds = self.ds_mission.copy()
        # Get indexes of where there are non-nan pressure values
        tloc_idx = np.where(~np.isnan(self.ds['pressure']))[0]
        # Select the times were thre are non-nan pressure values
        self.ds = self.ds.isel(time=tloc_idx)
        # Get all of the variables present in the dataset
        self.variable_names = list(self.ds.data_vars.keys())
        # Get all of the time values in the dataset
        self.time = self.ds.time.values
        # Get all of the pressure values in the dataset
        self.pres = self.ds.pressure.values
        # Get all of the lat and lon values in the dataset
        self.lon = np.nanmean(self.ds_mission.longitude)
        self.lat = np.nanmean(self.ds_mission.latitude[np.where(self.ds_mission.latitude.values<29.5)].values)

        self.initalize_grid()
    

    def initalize_grid(self):
        start_hour = int(pd.to_datetime(self.time[0]).hour / self.interval_h) * self.interval_h
        end_hour = int(pd.to_datetime(self.time[-1]).hour / self.interval_h) * self.interval_h
        start_time = pd.to_datetime(self.time[0]).replace(hour=start_hour, minute=0, second=0)
        end_time = pd.to_datetime(self.time[-1]).replace(hour=end_hour, minute=0, second=0)

        self.int_time = np.arange(start_time, end_time+np.timedelta64(self.interval_h, 'h'), np.timedelta64(self.interval_h, 'h')).astype('datetime64[s]')

        # create the pressure grids for intepolation
        start_pres = 0
        end_pres = np.nanmax(self.pres)
        self.int_pres = np.arange(start_pres, end_pres, self.interval_p)

        self.grid_pres,self.grid_time = np.meshgrid(self.int_pres,self.int_time[1:]) # get the time between two time point
        self.xx,self.yy = np.shape(self.grid_pres)

        # List of variable names
        var_names = ['int_temp', 'int_salt', 'int_cond', 'int_dens', 'int_turb', 'int_cdom', 'int_chlo', 'int_oxy4']

        # Dictionary to store the arrays
        self.data_arrays = {}

        # Initialize each array with NaN values and store it in the dictionary
        for var in var_names:
            self.data_arrays[var] = np.empty((self.xx, self.yy))
            self.data_arrays[var].fill(np.nan)
