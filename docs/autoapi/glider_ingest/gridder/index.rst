glider_ingest.gridder
=====================

.. py:module:: glider_ingest.gridder

.. autoapi-nested-parse::

   Module containing the Gridder class.



Classes
-------

.. autoapisummary::

   glider_ingest.gridder.Gridder


Module Contents
---------------

.. py:class:: Gridder

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


   .. py:method:: __attrs_post_init__()

      Initializes the Gridder class by copying the mission dataset, filtering valid pressures,
      extracting dataset dimensions, and initializing the time-pressure grid.



   .. py:method:: _calculate_derived_quantities()

      Calculate derived oceanographic quantities.

      Computed quantities:
          - Absolute salinity, conservative temperature, and potential temperature
          - Specific heat capacity, spiciness, and depth
      Derived quantities:
          - Heat content (HC): :math:`\Delta Z \cdot C_p \cdot T \cdot \rho`
          - Potential heat content (PHC): :math:`\Delta Z \cdot C_p \cdot (T - 26) \cdot \rho`, where values < 0 are set to NaN



   .. py:method:: _create_output_dataset(hc, phc, spc, dep)

      Create the final xarray Dataset with all variables.

      Output variables:
          - Gridded variables with `'g_'` prefix
          - g_hc: Heat content in kJ cm^{-2}
          - g_phc: Potential heat content in kJ cm^{-2}
          - g_sp: Spiciness
          - g_depth: Depth in meters



   .. py:method:: _handle_pressure_duplicates(tds)

      Handle duplicate pressure values by adding tiny offsets.

      Steps:
          - Identify duplicate pressure values
          - Add small incremental offsets to make values unique
          - Update time values to match new pressure values



   .. py:method:: _interpolate_variables()

      Interpolate variables to fixed pressure grid.

      Steps:
          - Select and process time slices
          - Interpolate each variable onto the fixed pressure grid



   .. py:method:: _process_time_slice(tds)

      Process a single time slice of data.

      Steps:
          - Sort data by pressure
          - Convert time coordinates to datetime64
          - Set time values to pressure values



   .. py:method:: add_attrs()

      Adds descriptive metadata attributes to the gridded dataset variables.

      This method assigns long names, units, valid ranges, and other metadata to the
      gridded dataset variables for better interpretation and standardization.



   .. py:method:: check_len(values, expected_length)

      Ensures that the length of the input array is greater than the expected length.

      Args:
          values (list | np.ndarray): Input array to check.
          expected_length (int): Minimum required length.

      Raises:
          ValueError: If the length of `values` is less than or equal to `expected_length`.



   .. py:method:: create_gridded_dataset() -> xarray.Dataset

      Process and interpolate time-sliced data to create a gridded dataset.

      This method orchestrates the complete gridding process by:
          1. Interpolating variables onto a fixed pressure grid
          2. Computing derived oceanographic quantities
          3. Creating the final dataset with standardized dimensions
          4. Adding metadata attributes

      Note:
          Requires the `gsw` library for oceanographic calculations and assumes
          that `self.data_arrays` and `self.int_time` are properly initialized.



   .. py:method:: initalize_grid()

      Creates a time-pressure grid for interpolation.

      This method calculates evenly spaced time intervals based on the `interval_h` attribute
      and pressure intervals based on the `interval_p` attribute. The resulting grids are stored
      as internal attributes for further processing.



   .. py:attribute:: data_arrays
      :type:  dict


   .. py:attribute:: ds
      :type:  xarray.Dataset


   .. py:attribute:: ds_gridded
      :type:  xarray.Dataset


   .. py:attribute:: ds_mission
      :type:  xarray.Dataset


   .. py:attribute:: grid_pres
      :type:  numpy.ndarray


   .. py:attribute:: grid_time
      :type:  numpy.ndarray


   .. py:attribute:: int_pres
      :type:  numpy.ndarray


   .. py:attribute:: int_time
      :type:  numpy.ndarray


   .. py:attribute:: interval_h
      :type:  int | float


   .. py:attribute:: interval_p
      :type:  int | float


   .. py:attribute:: lat
      :type:  numpy.ndarray


   .. py:attribute:: lon
      :type:  numpy.ndarray


   .. py:attribute:: pres
      :type:  numpy.ndarray


   .. py:attribute:: time
      :type:  numpy.ndarray


   .. py:attribute:: variable_names
      :type:  list


   .. py:attribute:: xx
      :type:  numpy.ndarray


   .. py:attribute:: yy
      :type:  numpy.ndarray


