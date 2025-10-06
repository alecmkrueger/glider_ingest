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

   .. attribute:: ds_mission

      The input mission dataset to process.

      :type: xr.Dataset

   .. attribute:: interval_h

      Time interval (in hours) for gridding.

      :type: int | float

   .. attribute:: interval_p

      Pressure interval (in decibars) for gridding.

      :type: int | float

   Internal Attributes (initialized later):
       ds (xr.Dataset): A copy of the mission dataset with NaN pressures removed.
       variable_names (list): List of variable names in the dataset.
       time, pres (np.ndarray): Arrays of time and pressure values.
       lat, lon (np.ndarray): Mean latitude and longitude of the dataset.
       grid_pres, grid_time (np.ndarray): Pressure and time grids for interpolation.
       data_arrays (dict): Dictionary of initialized gridded variables.


   .. py:method:: add_attrs()

      Adds descriptive metadata attributes to the gridded dataset variables.

      This method assigns long names, units, valid ranges, and other metadata to the
      gridded dataset variables for better interpretation and standardization.



   .. py:method:: check_len(values, expected_length)

      Ensures that the length of the input array is greater than the expected length.

      :param values: Input array to check.
      :type values: list | np.ndarray
      :param expected_length: Minimum required length.
      :type expected_length: int

      :raises ValueError: If the length of `values` is less than or equal to `expected_length`.



   .. py:method:: create_gridded_dataset() -> xarray.Dataset

      Process and interpolate time-sliced data to create a gridded dataset.

      This method orchestrates the complete gridding process by:
          1. Interpolating variables onto a fixed pressure grid
          2. Computing derived oceanographic quantities
          3. Creating the final dataset with standardized dimensions
          4. Adding metadata attributes

      .. note::

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


   .. py:property:: logger

      Get the logger instance for this gridder.


   .. py:attribute:: lon
      :type:  numpy.ndarray


   .. py:attribute:: pres
      :type:  numpy.ndarray


   .. py:attribute:: time
      :type:  numpy.ndarray


   .. py:attribute:: variable_names
      :type:  list


   .. py:attribute:: xx
      :type:  int


   .. py:attribute:: yy
      :type:  int


