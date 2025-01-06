'''
Module containing the Gridder class
'''
from attrs import define,field
import numpy as np
import pandas as pd
import xarray as xr
import gsw


@define
class Gridder:
    '''
    Class to create and calculate the gridded dataset.
    This class handles some functions that are coupled to make the code easier to read and maintain
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
        '''
        Initalize the class and get the dimension values of the dataset
        '''
        self.ds = self.ds_mission.copy()
        # Get indexes of where there are non-nan pressure values
        tloc_idx = np.where(~np.isnan(self.ds['pressure']))[0]
        # Select the times were thre are non-nan pressure values
        self.ds = self.ds.isel(time=tloc_idx)
        # Get all of the variables present in the dataset
        self.variable_names = list(self.ds.data_vars.keys())
        # Get all of the time values in the dataset
        self.time = self.ds.time.values
        self.check_len(self.time,1)
        # Get all of the pressure values in the dataset
        self.pres = self.ds.pressure.values
        # Get all of the lat and lon values in the dataset
        self.lon = np.nanmean(self.ds_mission.longitude.values)
        self.lat = np.nanmean(self.ds_mission.latitude.values)

        self.initalize_grid()
    
    def check_len(self,values,expected_length):
        '''Check if the length of a list is less than or equal to the expected length'''
        if len(values) <= expected_length:
            raise ValueError(f'Not enough values to grid {values}')
    
    def initalize_grid(self):
        '''
        Initalize the grid that is used to calcuate the gridded dataset
        '''
        start_hour = int(pd.to_datetime(self.time[0]).hour / self.interval_h) * self.interval_h
        end_hour = int(pd.to_datetime(self.time[-1]).hour / self.interval_h) * self.interval_h
        start_time = pd.to_datetime(self.time[0]).replace(hour=start_hour, minute=0, second=0)
        end_time = pd.to_datetime(self.time[-1]).replace(hour=end_hour, minute=0, second=0)

        self.int_time = np.arange(start_time, end_time+np.timedelta64(self.interval_h, 'h'), np.timedelta64(self.interval_h, 'h')).astype('datetime64[ns]')

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

    def add_attrs(self):
        '''
        Add dataset attributes to the gridded variables
        '''
        self.ds_gridded['g_temp'].attrs = {'long_name': 'Gridded Temperature',
        'observation_type': 'calculated',
        'source': 'temperature from sci_water_temp',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_temperature',
        'units': 'Celsius',
        'valid_max': 40.0,
        'valid_min': -5.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_salt'].attrs = {'long_name': 'Gridded Salinity',
        'observation_type': 'calculated',
        'source': 'salinity from sci_water_sal',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_practical_salinity',
        'units': '1',
        'valid_max': 40.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_cond'].attrs = {'long_name': 'Gridded Conductivity',
        'observation_type': 'calculated',
        'source': 'conductivity from sci_water_cond',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_electrical_conductivity',
        'units': 'S m-1',
        'valid_max': 10.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_dens'].attrs = {'long_name': 'Gridded Density',
        'observation_type': 'calculated',
        'source': 'density from sci_water_dens',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_density',
        'units': 'kg m-3',
        'valid_max': 1040.0,
        'valid_min': 1015.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # if 'turb' in self.variable_names:
        #     self.ds_gridded['g_turb'].attrs = {'long_name': 'Gridded Turbidity',
        #     'observation_type': 'calculated',
        #     'source': 'turbidity from sci_flbbcd_bb_units',
        #     'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        #     'standard_name': 'sea_water_turbidity',
        #     'units': '1',
        #     'valid_max': 1.0,
        #     'valid_min': 0.0,
        #     'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # if 'cdom' in self.variable_names:
        #     self.ds_gridded['g_cdom'].attrs = {'long_name': 'Gridded CDOM',
        #     'observation_type': 'calculated',
        #     'source': 'cdom from sci_flbbcd_cdom_units',
        #     'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        #     'standard_name': 'concentration_of_colored_dissolved_organic_matter_in_sea_water',
        #     'units': 'ppb',
        #     'valid_max': 50.0,
        #     'valid_min': 0.0,
        #     'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # if 'chlor' in self.variable_names:
        #     self.ds_gridded['g_chlo'].attrs = {'long_name': 'Gridded Chlorophyll_a',
        #     'observation_type': 'calculated',
        #     'source': 'chlorophyll from sci_flbbcd_chlor_units',
        #     'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        #     'standard_name': 'mass_concentration_of_chlorophyll_a_in_sea_water',
        #     'units': '\u03BCg/L',
        #     'valid_max': 10.0,
        #     'valid_min': 0.0,
        #     'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        if 'oxygen' in self.variable_names:
            self.ds_gridded['g_oxy4'].attrs = {'long_name': 'Gridded Oxygen',
            'observation_type': 'calculated',
            'source': 'oxygen from sci_oxy4_oxygen',
            'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
            'standard_name': 'moles_of_oxygen_per_unit_mass_in_sea_water',
            'units': '\u03BCmol/kg',
            'valid_max': 500.0,
            'valid_min': 0.0,
            'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_hc'].attrs = {'long_name': 'Gridded Heat Content',
        'observation_type': 'calculated',
        'source': 'g_temp, g_dens, cp=gsw.cp_t_exact, dz='+str(self.interval_p)+'dbar',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_heat_content_for_all_grids',
        'units': 'kJ/cm^2',
        'valid_max': 10.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_phc'].attrs = {'long_name': 'Gridded Potential Heat Content',
        'observation_type': 'calculated',
        'source': 'g_temp, g_dens, cp=gsw.cp_t_exact, dz='+str(self.interval_p)+'dbar',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_heat_content_for_grids_above_26°C',
        'units': 'kJ/cm^2',
        'valid_max': 10.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_sp'].attrs = {'long_name': 'Gridded Spiciness',
        'observation_type': 'calculated',
        'source': 'g_temp, g_salt, g_pres, lon, lat, via gsw.spiciness0',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'spiciness_from_absolute_salinity_and_conservative_temperature_at_0dbar',
        'units': 'kg/m^3',
        'valid_max': 10.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_depth'].attrs = {'long_name': 'Gridded Depth',
        'observation_type': 'calculated',
        'source': 'g_pres, lat, via gsw.z_from_p',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_depth',
        'units': 'm',
        'valid_max': 1000.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}

    def create_gridded_dataset(self):
        '''
        Calculate gridded data and create gridded dataset
        '''
        for ttt in range(self.xx):
            tds:xr.Dataset = self.ds.sel(time=slice(str(self.int_time[ttt]),str(self.int_time[ttt+1]))).copy()
            if len(tds.time) > 0:
                tds = tds.sortby('pressure')
                tds = tds.assign_coords(time=('time',tds.time.values.astype('datetime64[ns]')))
                tds['time'] = tds['pressure'].values
                
                # Remove duplicates and slightly modify if necessary by adding a tiny value
                unique_pressures, indices, counts = np.unique(tds['pressure'], return_index=True, return_counts=True)
                duplicates = unique_pressures[counts > 1]
                for pressure in duplicates:
                    rrr = np.where(tds['pressure'] == pressure)[0]
                    for rr in rrr:
                        modified_pressure = pressure + 0.000000000001*rr
                        tds['pressure'][rr] = modified_pressure
                tds['time'] = tds['pressure'].values # save new non-duplicates pressure
                self.data_arrays['int_temp'][ttt,:] = tds.temperature.interp(time=self.int_pres)
                self.data_arrays['int_salt'][ttt,:] = tds.salinity.interp(time=self.int_pres)
                self.data_arrays['int_cond'][ttt,:] = tds.conductivity.interp(time=self.int_pres)
                self.data_arrays['int_dens'][ttt,:] = tds.density.interp(time=self.int_pres)
                if 'oxygen' in self.variable_names:
                    self.data_arrays['int_oxy4'][ttt,:] = tds.oxygen.interp(time=self.int_pres)

        # give a dz instead of calculating the inter depth
        sa = gsw.SA_from_SP(self.data_arrays['int_salt'], self.grid_pres, self.lon, self.lat)
        pt = gsw.pt0_from_t(sa, self.data_arrays['int_temp'], self.grid_pres)
        ct = gsw.CT_from_pt(sa, pt)
        cp = gsw.cp_t_exact(sa, self.data_arrays['int_temp'], self.grid_pres) * 0.001 # from J/(kg*K) to kJ/(kg*°C) or use 3.85 as a constant?
        dep = gsw.z_from_p(self.grid_pres, self.lat, geo_strf_dyn_height=0, sea_surface_geopotential=0)
        spc = gsw.spiciness0(sa, ct)

        dz = self.interval_p
        hc = dz*cp*self.data_arrays['int_temp']*self.data_arrays['int_dens'] # deltaZ * Cp * temperature * density in the unit as $[kJ/m^2]$ * 10**-4 to $[kJ/cm^2]$
        phc = dz*cp*(self.data_arrays['int_temp']-26)*self.data_arrays['int_dens'] # deltaZ * Cp * temperature * density in the unit as $[kJ/m^2]$ * 10**-4 to $[kJ/cm^2]$
        phc[phc<0] = np.nan
        self.ds_gridded = xr.Dataset()
        self.ds_gridded['g_temp'] = xr.DataArray(self.data_arrays['int_temp'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_salt'] = xr.DataArray(self.data_arrays['int_salt'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_cond'] = xr.DataArray(self.data_arrays['int_cond'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_dens'] = xr.DataArray(self.data_arrays['int_dens'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        if 'oxygen' in self.variable_names:
            self.ds_gridded['g_oxy4'] = xr.DataArray(self.data_arrays['int_oxy4'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_hc'] = xr.DataArray(hc*10**-4,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_phc'] = xr.DataArray(phc*10**-4,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_sp'] = xr.DataArray(spc,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_depth'] = xr.DataArray(dep,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])

        self.add_attrs()
