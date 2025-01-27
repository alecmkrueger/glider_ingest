'''
Module containing the Gridder class.
'''
from attrs import define, field
import numpy as np
import pandas as pd
import xarray as xr
import gsw

@define
class Gridder:
    '''
    Class to create and calculate a gridded dataset from a mission dataset.

    This class provides methods for processing oceanographic data, creating time and pressure grids,
    interpolating data onto those grids, and adding metadata attributes to the gridded dataset.

    Attributes:
        ds_mission (xr.Dataset): The input mission dataset to process.
        interval_h (int | float): Time interval (in hours) for gridding.
        interval_p (int | float): Pressure interval (in decibars) for gridding.

    Internal Attributes (initialized later):
        ds (xr.Dataset): A copy of the mission dataset with NaN pressures removed.
        variable_names (list): List of variable names in the dataset.
        time, pres (np.ndarray): Arrays of time and pressure values.
        lat, lon (np.ndarray): Mean latitude and longitude of the dataset.
        grid_pres, grid_time (np.ndarray): Pressure and time grids for interpolation.
        data_arrays (dict): Dictionary of initialized gridded variables.
    '''

    ds_mission: xr.Dataset
    interval_h: int | float = field(default=1)  # Time interval for gridding in hours.
    interval_p: int | float = field(default=0.1)  # Pressure interval for gridding in decibars.

    # Attributes initialized post-construction.
    ds: xr.Dataset = field(init=False)
    ds_gridded: xr.Dataset = field(init=False)
    variable_names: list = field(init=False)
    time: np.ndarray = field(init=False)
    pres: np.ndarray = field(init=False)
    lat: np.ndarray = field(init=False)
    lon: np.ndarray = field(init=False)
    xx: np.ndarray = field(init=False)
    yy: np.ndarray = field(init=False)
    int_time: np.ndarray = field(init=False)
    int_pres: np.ndarray = field(init=False)
    data_arrays: dict = field(init=False)
    grid_pres: np.ndarray = field(init=False)
    grid_time: np.ndarray = field(init=False)

    def __attrs_post_init__(self):
        '''
        Initializes the Gridder class by copying the mission dataset, filtering valid pressures,
        extracting dataset dimensions, and initializing the time-pressure grid.
        '''
        self.ds = self.ds_mission.copy()
        
        # Identify indexes of valid (non-NaN) pressure values.
        tloc_idx = np.where(~np.isnan(self.ds['pressure']))[0]
        
        # Select times corresponding to valid pressures.
        self.ds = self.ds.isel(time=tloc_idx)

        # Extract variable names and time/pressure values.
        self.variable_names = list(self.ds.data_vars.keys())
        self.time = self.ds.time.values
        self.check_len(self.time, 1)  # Ensure there is sufficient data to grid.
        self.pres = self.ds.pressure.values

        # Calculate mean latitude and longitude.
        self.lon = np.nanmean(self.ds_mission.longitude.values)
        self.lat = np.nanmean(self.ds_mission.latitude.values)

        # Initialize the time-pressure grid.
        self.initalize_grid()

    def check_len(self, values, expected_length):
        '''
        Ensures that the length of the input array is greater than the expected length.

        Args:
            values (list | np.ndarray): Input array to check.
            expected_length (int): Minimum required length.

        Raises:
            ValueError: If the length of `values` is less than or equal to `expected_length`.
        '''
        if len(values) <= expected_length:
            raise ValueError(f'Not enough values to grid {values}')

    def initalize_grid(self):
        '''
        Creates a time-pressure grid for interpolation.

        This method calculates evenly spaced time intervals based on the `interval_h` attribute
        and pressure intervals based on the `interval_p` attribute. The resulting grids are stored
        as internal attributes for further processing.
        '''
        # Define the start and end times rounded to the nearest interval.
        start_hour = int(pd.to_datetime(self.time[0]).hour / self.interval_h) * self.interval_h
        end_hour = int(pd.to_datetime(self.time[-1]).hour / self.interval_h) * self.interval_h
        start_time = pd.to_datetime(self.time[0]).replace(hour=start_hour, minute=0, second=0)
        end_time = pd.to_datetime(self.time[-1]).replace(hour=end_hour, minute=0, second=0)

        # Generate an array of evenly spaced time intervals.
        self.int_time = np.arange(start_time, end_time + np.timedelta64(self.interval_h, 'h'),
                                  np.timedelta64(self.interval_h, 'h')).astype('datetime64[ns]')

        # Create evenly spaced pressure intervals.
        start_pres = 0  # Start pressure in dbar.
        end_pres = np.nanmax(self.pres)  # Maximum pressure in dataset.
        self.int_pres = np.arange(start_pres, end_pres, self.interval_p)

        # Generate the pressure-time grid using a meshgrid.
        self.grid_pres, self.grid_time = np.meshgrid(self.int_pres, self.int_time[1:])
        self.xx, self.yy = np.shape(self.grid_pres)  # Dimensions of the grid.

        # Initialize arrays for gridded variables.
        var_names = []
        for varname in self.variable_names:
            if 'to_grid' in self.ds[varname].attrs.keys():
                if self.ds[varname].attrs['to_grid']:
                    var_names.extend([f'int_{varname}'])
        self.data_arrays = {}

        for var in var_names:
            # Initialize empty arrays with NaN values for each variable.
            self.data_arrays[var] = np.empty((self.xx, self.yy))
            self.data_arrays[var].fill(np.nan)

    def add_attrs(self):
        '''
        Adds descriptive metadata attributes to the gridded dataset variables.

        This method assigns long names, units, valid ranges, and other metadata to the
        gridded dataset variables for better interpretation and standardization.
        '''
        from glider_ingest.gridded_attrs import generate_variables
        variables = generate_variables(self.interval_h,self.interval_p)
        for var_short_name,variable in variables.items():
            if var_short_name in self.ds_gridded.data_vars.keys():
                self.ds_gridded[var_short_name].attrs = variable.to_dict()
        
        # self.ds_gridded['g_temperature'].attrs = {'long_name': 'Gridded Temperature',
        # 'observation_type': 'calculated',
        # 'source': 'temperature from sci_water_temp',
        # 'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        # 'standard_name': 'sea_water_temperature',
        # 'units': 'Celsius',
        # 'valid_max': 40.0,
        # 'valid_min': -5.0,
        # 'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # self.ds_gridded['g_salinity'].attrs = {'long_name': 'Gridded Salinity',
        # 'observation_type': 'calculated',
        # 'source': 'salinity from sci_water_sal',
        # 'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        # 'standard_name': 'sea_water_practical_salinity',
        # 'units': '1',
        # 'valid_max': 40.0,
        # 'valid_min': 0.0,
        # 'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # self.ds_gridded['g_conductivity'].attrs = {'long_name': 'Gridded Conductivity',
        # 'observation_type': 'calculated',
        # 'source': 'conductivity from sci_water_cond',
        # 'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        # 'standard_name': 'sea_water_electrical_conductivity',
        # 'units': 'S m-1',
        # 'valid_max': 10.0,
        # 'valid_min': 0.0,
        # 'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # self.ds_gridded['g_density'].attrs = {'long_name': 'Gridded Density',
        # 'observation_type': 'calculated',
        # 'source': 'density from sci_water_dens',
        # 'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        # 'standard_name': 'sea_water_density',
        # 'units': 'kg m-3',
        # 'valid_max': 1040.0,
        # 'valid_min': 1015.0,
        # 'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # if 'turb' in self.variable_names:
        #     self.ds_gridded['g_turbidity'].attrs = {'long_name': 'Gridded Turbidity',
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
        #     self.ds_gridded['g_chlorophyll'].attrs = {'long_name': 'Gridded Chlorophyll_a',
        #     'observation_type': 'calculated',
        #     'source': 'chlorophyll from sci_flbbcd_chlor_units',
        #     'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        #     'standard_name': 'mass_concentration_of_chlorophyll_a_in_sea_water',
        #     'units': '\u03BCg/L',
        #     'valid_max': 10.0,
        #     'valid_min': 0.0,
        #     'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # if 'oxygen' in self.variable_names:
        #     self.ds_gridded['g_oxygen'].attrs = {'long_name': 'Gridded Oxygen',
        #     'observation_type': 'calculated',
        #     'source': 'oxygen from sci_oxy4_oxygen',
        #     'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        #     'standard_name': 'moles_of_oxygen_per_unit_mass_in_sea_water',
        #     'units': '\u03BCmol/kg',
        #     'valid_max': 500.0,
        #     'valid_min': 0.0,
        #     'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # self.ds_gridded['g_hc'].attrs = {'long_name': 'Gridded Heat Content',
        # 'observation_type': 'calculated',
        # 'source': 'g_temp, g_dens, cp=gsw.cp_t_exact, dz='+str(self.interval_p)+'dbar',
        # 'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        # 'standard_name': 'sea_water_heat_content_for_all_grids',
        # 'units': 'kJ/cm^2',
        # 'valid_max': 10.0,
        # 'valid_min': 0.0,
        # 'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # self.ds_gridded['g_phc'].attrs = {'long_name': 'Gridded Potential Heat Content',
        # 'observation_type': 'calculated',
        # 'source': 'g_temp, g_dens, cp=gsw.cp_t_exact, dz='+str(self.interval_p)+'dbar',
        # 'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        # 'standard_name': 'sea_water_heat_content_for_grids_above_26°C',
        # 'units': 'kJ/cm^2',
        # 'valid_max': 10.0,
        # 'valid_min': 0.0,
        # 'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # self.ds_gridded['g_sp'].attrs = {'long_name': 'Gridded Spiciness',
        # 'observation_type': 'calculated',
        # 'source': 'g_temp, g_salt, g_pres, lon, lat, via gsw.spiciness0',
        # 'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        # 'standard_name': 'spiciness_from_absolute_salinity_and_conservative_temperature_at_0dbar',
        # 'units': 'kg/m^3',
        # 'valid_max': 10.0,
        # 'valid_min': 0.0,
        # 'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # self.ds_gridded['g_depth'].attrs = {'long_name': 'Gridded Depth',
        # 'observation_type': 'calculated',
        # 'source': 'g_pres, lat, via gsw.z_from_p',
        # 'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        # 'standard_name': 'sea_water_depth',
        # 'units': 'm',
        # 'valid_max': 1000.0,
        # 'valid_min': 0.0,
        # 'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}

    def create_gridded_dataset(self):
        """
        Process and interpolate time-sliced data to create a gridded dataset.

        This method iterates through time slices, processes data for each slice, 
        and interpolates variables like temperature, salinity, conductivity, 
        density, and optionally oxygen, onto a pressure-based grid. Additional 
        calculations for derived quantities such as spiciness, potential heat 
        content, and depth are performed. The results are stored in an 
        `xarray.Dataset` with standardized dimensions.

        Steps:
            - Select and sort data for each time slice
            - Handle duplicate pressure values by adjusting slightly to ensure uniqueness
            - Interpolate data variables onto a fixed pressure grid
            - Compute derived quantities:
                - Absolute salinity, conservative temperature, and potential temperature
                - Specific heat capacity, spiciness, and depth
                - Heat content and potential heat content
            - Assemble results into an `xarray.Dataset` with standardized dimensions and attributes

        Derived quantities:
            - Heat content (HC): :math:`\\Delta Z \\cdot C_p \\cdot T \\cdot \\rho`
            - Potential heat content (PHC): :math:`\\Delta Z \\cdot C_p \\cdot (T - 26) \\cdot \\rho`, where values < 0 are set to NaN

        Attributes:
            self.ds_gridded: The resulting gridded dataset with variables:
                - gridded variables depending on the varible settings, to_grid attribute in the Variable class
                - g_hc: Heat content in kJ cm^{-2}
                - g_phc: Potential heat content in kJ cm^{-2}
                - g_sp: Spiciness
                - g_depth: Depth in meters

        Note:
            Requires the `gsw` library for oceanographic calculations and assumes 
            that `self.data_arrays` and `self.int_time` are properly initialized.
        """


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
                # Interpolate to a fixed pressure grid
                for data_array_key,value in self.data_arrays.items():
                    if data_array_key in self.variable_names:
                        tds_key = data_array_key.replace('int_','')
                        self.data_arrays[data_array_key][ttt,:] = tds[tds_key].interp(time=self.int_pres)
                # if 'oxygen' in self.variable_names:
                #     self.data_arrays['int_oxygen'][ttt,:] = tds.oxygen.interp(time=self.int_pres)

        # give a dz instead of calculating the inter depth
        sa = gsw.SA_from_SP(self.data_arrays['int_salinity'], self.grid_pres, self.lon, self.lat)
        pt = gsw.pt0_from_t(sa, self.data_arrays['int_temperature'], self.grid_pres)
        ct = gsw.CT_from_pt(sa, pt)
        cp = gsw.cp_t_exact(sa, self.data_arrays['int_temperature'], self.grid_pres) * 0.001 # from J/(kg*K) to kJ/(kg*°C) or use 3.85 as a constant?
        dep = gsw.z_from_p(self.grid_pres, self.lat, geo_strf_dyn_height=0, sea_surface_geopotential=0)
        spc = gsw.spiciness0(sa, ct)

        dz = self.interval_p
        hc = dz*cp*self.data_arrays['int_temperature']*self.data_arrays['int_density'] # deltaZ * Cp * temperature * density in the unit as $[kJ/m^2]$ * 10**-4 to $[kJ/cm^2]$
        phc = dz*cp*(self.data_arrays['int_temperature']-26)*self.data_arrays['int_density'] # deltaZ * Cp * temperature * density in the unit as $[kJ/m^2]$ * 10**-4 to $[kJ/cm^2]$
        phc[phc<0] = np.nan
        self.ds_gridded = xr.Dataset()
        for data_array_key,value in self.data_arrays.items():
            if data_array_key in self.variable_names:
                self.ds_gridded[data_array_key] = xr.DataArray(value,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
                
        gridded_vars = [varname.replace('int_','g_') for varname in self.data_arrays.keys()]
        for gridded_var in gridded_vars:
            self.ds_gridded[gridded_var] = xr.DataArray(self.data_arrays[gridded_var.replace('g_','int_')],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        # self.ds_gridded['g_temp'] = xr.DataArray(self.data_arrays['int_temperature'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        # self.ds_gridded['g_salt'] = xr.DataArray(self.data_arrays['int_salinity'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        # self.ds_gridded['g_cond'] = xr.DataArray(self.data_arrays['int_conductivity'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        # self.ds_gridded['g_dens'] = xr.DataArray(self.data_arrays['int_density'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        # if 'oxygen' in self.variable_names:
        #     self.ds_gridded['g_oxy4'] = xr.DataArray(self.data_arrays['int_oxygen'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
            
        self.ds_gridded['g_hc'] = xr.DataArray(hc*10**-4,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_phc'] = xr.DataArray(phc*10**-4,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_sp'] = xr.DataArray(spc,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_depth'] = xr.DataArray(dep,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])

        self.add_attrs()
