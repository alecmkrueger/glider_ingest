'''
Module containing the Gridder class.
'''
from attrs import define, field
import numpy as np
import pandas as pd
import xarray as xr
import gsw
import logging

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
    xx: int = field(init=False)
    yy: int = field(init=False)
    int_time: np.ndarray = field(init=False)
    int_pres: np.ndarray = field(init=False)
    data_arrays: dict = field(init=False)
    grid_pres: np.ndarray = field(init=False)
    grid_time: np.ndarray = field(init=False)

    @property
    def logger(self):
        """Get the logger instance for this gridder."""
        return logging.getLogger('glider_ingest')

    def __attrs_post_init__(self):
        '''
        Initializes the Gridder class by copying the mission dataset, filtering valid pressures,
        extracting dataset dimensions, and initializing the time-pressure grid.
        '''
        self.logger.info("Initializing Gridder with intervals: %dh time, %.1f dbar pressure",
                        self.interval_h, self.interval_p)

        self.ds = self.ds_mission.copy()
        initial_time_points = len(self.ds.time)
        self.logger.debug("Initial dataset contains %d time points", initial_time_points)

        # Identify indexes of valid (non-NaN) pressure values.
        tloc_idx = np.where(~np.isnan(self.ds['pressure']))[0]
        valid_pressure_points = len(tloc_idx)
        self.logger.debug("Found %d valid pressure values out of %d total points (%.1f%%)",
                        valid_pressure_points, initial_time_points,
                        100 * valid_pressure_points / initial_time_points if initial_time_points > 0 else 0)

        # Select times corresponding to valid pressures.
        self.ds = self.ds.isel(time=tloc_idx)

        # Extract variable names and time/pressure values.
        self.variable_names = list(self.ds.data_vars.keys())
        self.logger.debug("Dataset variables: %s", self.variable_names)

        self.time = self.ds.time.values
        self.check_len(self.time, 1)  # Ensure there is sufficient data to grid.
        self.pres = self.ds.pressure.values

        pressure_range = (np.nanmin(self.pres), np.nanmax(self.pres))
        time_range = (self.time[0], self.time[-1])
        self.logger.debug("Pressure range: %.2f - %.2f dbar", pressure_range[0], pressure_range[1])
        self.logger.debug("Time range: %s - %s", pd.to_datetime(time_range[0]), pd.to_datetime(time_range[1]))

        # Calculate mean latitude and longitude.
        self.lon = np.nanmean(self.ds_mission.longitude.values)
        self.lat = np.nanmean(self.ds_mission.latitude.values)
        self.logger.debug("Mean position: %.4f°N, %.4f°E", self.lat, self.lon)

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
        self.logger.debug("Checking array length: %d values (minimum required: %d)",
                         len(values), expected_length)
        if len(values) <= expected_length:
            self.logger.error("Insufficient data for gridding: %d values (need > %d)",
                            len(values), expected_length)
            raise ValueError(f'Not enough values to grid {values}')
        self.logger.debug("Array length check passed")

    def initalize_grid(self):
        '''
        Creates a time-pressure grid for interpolation.

        This method calculates evenly spaced time intervals based on the `interval_h` attribute
        and pressure intervals based on the `interval_p` attribute. The resulting grids are stored
        as internal attributes for further processing.
        '''
        self.logger.info("Creating time-pressure grid")

        # Define the start and end times rounded to the nearest interval.
        start_hour = int(pd.to_datetime(self.time[0]).hour / self.interval_h) * self.interval_h
        end_hour = int(pd.to_datetime(self.time[-1]).hour / self.interval_h) * self.interval_h
        start_time = pd.to_datetime(self.time[0]).replace(hour=start_hour, minute=0, second=0)
        end_time = pd.to_datetime(self.time[-1]).replace(hour=end_hour, minute=0, second=0)

        self.logger.debug("Grid time bounds: %s to %s", start_time, end_time)

        # Generate an array of evenly spaced time intervals.
        self.int_time = np.arange(
            start_time,
            end_time + np.timedelta64(int(self.interval_h), 'h'),
            np.timedelta64(int(self.interval_h), 'h')
        ).astype('datetime64[ns]')

        self.logger.info("Created %d time intervals with %dh spacing", len(self.int_time), self.interval_h)

        # Create evenly spaced pressure intervals.
        start_pres = 0  # Start pressure in dbar.
        end_pres = np.nanmax(self.pres)  # Maximum pressure in dataset.
        self.int_pres = np.arange(start_pres, end_pres, self.interval_p)

        self.logger.debug("Created %d pressure levels from %.1f to %.1f dbar (%.1f dbar spacing)",
                        len(self.int_pres), start_pres, end_pres, self.interval_p)

        # Generate the pressure-time grid using a meshgrid.
        self.grid_pres, self.grid_time = np.meshgrid(self.int_pres, self.int_time[1:])
        self.xx, self.yy = np.shape(self.grid_pres)  # Dimensions of the grid.

        self.logger.debug("Grid dimensions: %d time x %d pressure = %d total points",
                        self.xx, self.yy, self.xx * self.yy)

        # Initialize variables for grid interpolation.
        gridded_vars = [varname for varname in self.variable_names
                       if self.ds[varname].attrs.get('to_grid') in [True, 'True']]

        self.logger.info("Variables to grid: %s", gridded_vars)
        self.logger.debug("Variables not gridded: %s",
                         [v for v in self.variable_names if v not in gridded_vars])

        var_names = [f'int_{varname}' for varname in gridded_vars]

        # Initialize data arrays with NaN values
        self.data_arrays = {
            var: np.full((self.xx, self.yy), np.nan)
            for var in var_names
        }

        self.logger.debug("Initialized %d data arrays for interpolation", len(self.data_arrays))


    def add_attrs(self):
        '''
        Adds descriptive metadata attributes to the gridded dataset variables.

        This method assigns long names, units, valid ranges, and other metadata to the
        gridded dataset variables for better interpretation and standardization.
        '''
        self.logger.debug("Adding metadata attributes to gridded variables")

        from .gridded_attrs import generate_variables
        variables = generate_variables(self.interval_h,self.interval_p)

        attrs_added = 0
        for var_short_name,variable in variables.items():
            if var_short_name in self.ds_gridded.data_vars.keys():
                self.ds_gridded[var_short_name].attrs = variable.to_dict()
                attrs_added += 1
                self.logger.debug("Added attributes to variable: %s", var_short_name)

        self.logger.info("Added metadata attributes to %d variables", attrs_added)

    def _process_time_slice(self, tds):
        """
        Process a single time slice of data.

        Steps:
            - Sort data by pressure
            - Replace time coordinate with pressure values for interpolation
        """
        if len(tds.time) == 0:
            self.logger.debug("Empty time slice encountered")
            return tds

        initial_points = len(tds.time)
        pressure_range = (tds.pressure.min().values, tds.pressure.max().values)
        self.logger.debug("Processing time slice with %d points, pressure range: %.2f-%.2f dbar",
                         initial_points, pressure_range[0], pressure_range[1])

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

        if len(duplicates) > 0:
            total_duplicates = sum(counts[counts > 1]) - len(duplicates)
            self.logger.debug("Found %d duplicate pressure values affecting %d points",
                            len(duplicates), total_duplicates)

            for time_val in duplicates:
                indices = np.where(time_coords == time_val)[0]
                self.logger.debug("Resolving %d duplicates at pressure %.6f", len(indices), time_val)
                for i, idx in enumerate(indices):
                    time_coords[idx] = time_val + 0.000000000001 * i

            # Update time coordinate with the modified values
            tds = tds.assign_coords(time=('time', time_coords))
        else:
            self.logger.debug("No duplicate pressure values found")

        return tds

    def _interpolate_variables(self):
        """
        Interpolate variables to fixed pressure grid.

        Steps:
            - Select and process time slices
            - Interpolate each variable onto the fixed pressure grid
        """
        self.logger.info("Starting interpolation for %d time slices", self.xx)

        empty_slices = 0
        processed_slices = 0

        for ttt in range(self.xx):
            self.logger.debug("Processing time slice %d/%d: %s to %s",
                            ttt + 1, self.xx, self.int_time[ttt], self.int_time[ttt+1])

            tds = self.ds.sel(time=slice(str(self.int_time[ttt]), str(self.int_time[ttt+1]))).copy()

            # Skip empty time slices
            if len(tds.time) == 0:
                self.logger.debug("Time slice %d is empty, filling with NaN", ttt + 1)
                empty_slices += 1
                # Fill with NaN values for this time slice
                for data_array_key in self.data_arrays.keys():
                    self.data_arrays[data_array_key][ttt,:] = np.nan
                continue

            tds = self._process_time_slice(tds)
            processed_slices += 1

            # Interpolate each variable
            vars_interpolated = 0
            for data_array_key, value in self.data_arrays.items():
                tds_key = data_array_key.replace('int_', '')

                # Check if the variable exists in the time slice
                if tds_key in tds:
                    try:
                        self.data_arrays[data_array_key][ttt,:] = tds[tds_key].interp(time=self.int_pres)
                        vars_interpolated += 1
                    except Exception as e:
                        self.logger.warning("Interpolation failed for %s in slice %d: %s",
                                          tds_key, ttt + 1, str(e))
                        self.data_arrays[data_array_key][ttt,:] = np.nan
                else:
                    self.logger.debug("Variable %s not found in slice %d, filling with NaN",
                                    tds_key, ttt + 1)
                    # Fill with NaN if variable doesn't exist
                    self.data_arrays[data_array_key][ttt,:] = np.nan

            if ttt % max(1, self.xx // 10) == 0:  # Log progress every 10%
                progress = 100 * (ttt + 1) / self.xx
                self.logger.info("Interpolation progress: %.1f%% (%d/%d slices)",
                               progress, ttt + 1, self.xx)

        self.logger.info("Interpolation complete: %d processed, %d empty slices",
                        processed_slices, empty_slices)

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
        self.logger.info("Calculating derived oceanographic quantities")

        # Check for required variables
        required_vars = ['int_salinity', 'int_temperature', 'int_density']
        missing_vars = [var for var in required_vars if var not in self.data_arrays]

        if missing_vars:
            self.logger.error("Missing required variables for derived calculations: %s", missing_vars)
            raise ValueError(f"Cannot calculate derived quantities: missing {missing_vars}")

        self.logger.debug("Computing absolute salinity from practical salinity")
        sa = gsw.SA_from_SP(self.data_arrays['int_salinity'], self.grid_pres, self.lon, self.lat)

        self.logger.debug("Computing potential temperature")
        pt = gsw.pt0_from_t(sa, self.data_arrays['int_temperature'], self.grid_pres)

        self.logger.debug("Computing conservative temperature")
        ct = gsw.CT_from_pt(sa, pt)

        self.logger.debug("Computing specific heat capacity")
        cp = gsw.cp_t_exact(sa, self.data_arrays['int_temperature'], self.grid_pres) * 0.001

        self.logger.debug("Computing depth from pressure")
        dep = gsw.z_from_p(self.grid_pres, self.lat, geo_strf_dyn_height=0, sea_surface_geopotential=0)

        self.logger.debug("Computing spiciness")
        spc = gsw.spiciness0(sa, ct)

        self.logger.debug("Computing heat content and potential heat content")
        dz = self.interval_p
        hc = dz * cp * self.data_arrays['int_temperature'] * self.data_arrays['int_density']
        phc = dz * cp * (self.data_arrays['int_temperature'] - 26) * self.data_arrays['int_density']

        # Count negative PHC values before setting to NaN
        negative_phc_count = np.sum(phc < 0)
        total_phc_count = np.size(phc)
        phc[phc < 0] = np.nan

        self.logger.debug("Set %d negative PHC values to NaN (%.1f%% of total)",
                        negative_phc_count, 100 * negative_phc_count / total_phc_count)

        # Log value ranges for key quantities
        self.logger.debug("Heat content range: %.2e to %.2e J/m³", np.nanmin(hc), np.nanmax(hc))
        self.logger.debug("Potential heat content range: %.2e to %.2e J/m³", np.nanmin(phc), np.nanmax(phc))
        self.logger.debug("Spiciness range: %.3f to %.3f", np.nanmin(spc), np.nanmax(spc))
        self.logger.debug("Depth range: %.1f to %.1f m", np.nanmin(dep), np.nanmax(dep))

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
        self.logger.info("Creating output gridded dataset")

        self.ds_gridded = xr.Dataset()

        # Add interpolated variables
        interpolated_vars = 0
        for data_array_key, value in self.data_arrays.items():
            base_key = data_array_key.replace('int_', '')
            if base_key in self.variable_names:
                gridded_var = f'g_{base_key}'
                self.ds_gridded[gridded_var] = xr.DataArray(
                    value,
                    [('g_time', self.int_time[1:]), ('g_pres', self.int_pres)]
                )
                interpolated_vars += 1
                self.logger.debug("Added gridded variable: %s", gridded_var)

        self.logger.info("Added %d interpolated variables to dataset", interpolated_vars)

        # Add derived variables
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
            self.logger.debug("Added derived variable: %s", var_name)

        self.logger.info("Added %d derived variables to dataset", len(derived_vars))

        total_vars = len(self.ds_gridded.data_vars)
        grid_size = len(self.int_time[1:]) * len(self.int_pres)
        self.logger.debug("Final gridded dataset: %d variables on %dx%d grid (%d total points)",
                        total_vars, len(self.int_time[1:]), len(self.int_pres), grid_size)

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
        self.logger.info("=== Starting gridded dataset creation ===")
        start_time = pd.Timestamp.now()

        try:
            self.logger.info("Step 1/4: Interpolating variables to grid")
            self._interpolate_variables()

            self.logger.info("Step 2/4: Computing derived oceanographic quantities")
            hc, phc, spc, dep = self._calculate_derived_quantities()

            self.logger.info("Step 3/4: Creating output dataset")
            self._create_output_dataset(hc, phc, spc, dep)

            self.logger.info("Step 4/4: Adding metadata attributes")
            self.add_attrs()

            processing_time = pd.Timestamp.now() - start_time
            self.logger.info("=== Gridded dataset creation complete in %.2f seconds ===",
                           processing_time.total_seconds())

            # Log final dataset summary
            nan_percentage = 100 * np.isnan(list(self.ds_gridded.data_vars.values())[0].values).sum() / self.ds_gridded.sizes['g_time'] / self.ds_gridded.sizes['g_pres']
            self.logger.debug("Dataset completeness: %.1f%% valid data points", 100 - nan_percentage)

            return self.ds_gridded

        except Exception as e:
            self.logger.error("Gridded dataset creation failed: %s", str(e))
            raise
