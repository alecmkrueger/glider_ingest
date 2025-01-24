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



   .. py:method:: create_gridded_dataset()

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
          - Heat content (HC): :math:`\Delta Z \cdot C_p \cdot T \cdot \rho`
          - Potential heat content (PHC): :math:`\Delta Z \cdot C_p \cdot (T - 26) \cdot \rho`, where values < 0 are set to NaN

      Attributes:
          self.ds_gridded: The resulting gridded dataset with variables:
              - g_temp: Gridded temperature
              - g_salt: Gridded salinity
              - g_cond: Gridded conductivity
              - g_dens: Gridded density
              - g_oxy4: Gridded oxygen (if available)
              - g_hc: Heat content in kJ cm^{-2}
              - g_phc: Potential heat content in kJ cm^{-2}
              - g_sp: Spiciness
              - g_depth: Depth in meters

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


