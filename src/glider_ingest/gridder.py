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

    Depends on the dataset having attributes
    ----------------------------------------

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

        # Initialize variables for grid interpolation.
        var_names = [
            f'int_{varname}'
            for varname in self.variable_names
            if self.ds[varname].attrs.get('to_grid') in [True, 'True']
        ]

        # Initialize data arrays with NaN values
        self.data_arrays = {
            var: np.full((self.xx, self.yy), np.nan)
            for var in var_names
        }


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

    def _process_time_slice(self, tds):
        """
        Process a single time slice of data.

        Steps:
            - Sort data by pressure
            - Replace time coordinate with pressure values for interpolation
        """
        if len(tds.time) == 0:
            return tds

        tds = tds.sortby('pressure')
        # Replace time coordinate with pressure values for interpolation
        tds = tds.assign_coords(time=('time', tds['pressure'].values))
        return self._handle_pressure_duplicates(tds)

    def _handle_pressure_duplicates(self, tds):
        """
        Handle duplicate pressure values by adding tiny offsets.

        Steps:
            - Identify duplicate time coordinate values (which are pressure values)
            - Add small incremental offsets to make values unique
            - Update time coordinate to match new pressure values
        """
        time_coords = tds.time.values.copy()
        unique_times, indices, counts = np.unique(time_coords, return_index=True, return_counts=True)
        duplicates = unique_times[counts > 1]

        for time_val in duplicates:
            indices = np.where(time_coords == time_val)[0]
            for i, idx in enumerate(indices):
                time_coords[idx] = time_val + 0.000000000001 * i

        # Update time coordinate with the modified values
        tds = tds.assign_coords(time=('time', time_coords))
        return tds

    def _interpolate_variables(self):
        """
        Interpolate variables to fixed pressure grid.

        Steps:
            - Select and process time slices
            - Interpolate each variable onto the fixed pressure grid
        """
        for ttt in range(self.xx):
            print(f"Processing time slice {ttt+1}/{self.xx}")
            print(f"Time slice start: {self.int_time[ttt]}, end: {self.int_time[ttt+1]}")

            tds = self.ds.sel(time=slice(str(self.int_time[ttt]), str(self.int_time[ttt+1]))).copy()
            print(f"Time slice length: {len(tds.time)}")

            # Skip empty time slices
            if len(tds.time) == 0:
                print(f"Skipping empty time slice {ttt+1}")
                # Fill with NaN values for this time slice
                for data_array_key in self.data_arrays.keys():
                    self.data_arrays[data_array_key][ttt,:] = np.nan
                continue

            tds = self._process_time_slice(tds)

            for data_array_key, value in self.data_arrays.items():
                tds_key = data_array_key.replace('int_', '')
                print(f"Interpolating variable: {tds_key} for time slice {ttt+1}/{self.xx}")

                # Check if the variable exists in the time slice
                if tds_key in tds:
                    self.data_arrays[data_array_key][ttt,:] = tds[tds_key].interp(time=self.int_pres)
                else:
                    # Fill with NaN if variable doesn't exist
                    self.data_arrays[data_array_key][ttt,:] = np.nan

    def _calculate_derived_quantities(self):
        """
        Calculate derived oceanographic quantities.

        Computed quantities:
            - Absolute salinity, conservative temperature, and potential temperature
            - Specific heat capacity, spiciness, and depth
        Derived quantities:
            - Heat content (HC): :math:`\\Delta Z \\cdot C_p \\cdot T \\cdot \\rho`
            - Potential heat content (PHC): :math:`\\Delta Z \\cdot C_p \\cdot (T - 26) \\cdot \\rho`, where values < 0 are set to NaN
        """
        sa = gsw.SA_from_SP(self.data_arrays['int_salinity'], self.grid_pres, self.lon, self.lat)
        pt = gsw.pt0_from_t(sa, self.data_arrays['int_temperature'], self.grid_pres)
        ct = gsw.CT_from_pt(sa, pt)
        cp = gsw.cp_t_exact(sa, self.data_arrays['int_temperature'], self.grid_pres) * 0.001
        dep = gsw.z_from_p(self.grid_pres, self.lat, geo_strf_dyn_height=0, sea_surface_geopotential=0)
        spc = gsw.spiciness0(sa, ct)

        dz = self.interval_p
        hc = dz * cp * self.data_arrays['int_temperature'] * self.data_arrays['int_density']
        phc = dz * cp * (self.data_arrays['int_temperature'] - 26) * self.data_arrays['int_density']
        phc[phc < 0] = np.nan

        return hc, phc, spc, dep

    def _create_output_dataset(self, hc, phc, spc, dep):
        """
        Create the final xarray Dataset with all variables.

        Output variables:
            - Gridded variables with `'g_'` prefix
            - g_hc: Heat content in kJ cm^{-2}
            - g_phc: Potential heat content in kJ cm^{-2}
            - g_sp: Spiciness
            - g_depth: Depth in meters
        """
        self.ds_gridded = xr.Dataset()

        for data_array_key, value in self.data_arrays.items():
            base_key = data_array_key.replace('int_', '')
            if base_key in self.variable_names:
                # print('adding gridded data to xarray', base_key)
                gridded_var = f'g_{base_key}'
                self.ds_gridded[gridded_var] = xr.DataArray(
                    value,
                    [('g_time', self.int_time[1:]), ('g_pres', self.int_pres)]
                )

        derived_vars = {
            'g_hc': hc * 10**-4,
            'g_phc': phc * 10**-4,
            'g_sp': spc,
            'g_depth': dep
        }

        for var_name, data in derived_vars.items():
            self.ds_gridded[var_name] = xr.DataArray(
                data,
                [('g_time', self.int_time[1:]), ('g_pres', self.int_pres)]
            )

    def create_gridded_dataset(self) -> xr.Dataset:
        """
        Process and interpolate time-sliced data to create a gridded dataset.

        This method orchestrates the complete gridding process by:
            1. Interpolating variables onto a fixed pressure grid
            2. Computing derived oceanographic quantities
            3. Creating the final dataset with standardized dimensions
            4. Adding metadata attributes

        Note:
            Requires the `gsw` library for oceanographic calculations and assumes
            that `self.data_arrays` and `self.int_time` are properly initialized.
        """
        self._interpolate_variables()
        hc, phc, spc, dep = self._calculate_derived_quantities()
        self._create_output_dataset(hc, phc, spc, dep)
        self.add_attrs()
        return self.ds_gridded
