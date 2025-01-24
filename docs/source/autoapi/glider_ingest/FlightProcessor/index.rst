glider_ingest.FlightProcessor
=============================

.. py:module:: glider_ingest.FlightProcessor


Classes
-------

.. autoapisummary::

   glider_ingest.FlightProcessor.FlightProcessor


Module Contents
---------------

.. py:class:: FlightProcessor

   A class to process flight data from gliders.

   The data is loaded from DBD files, converted to pandas DataFrames, and then 
   transformed into xarray Datasets with metadata attributes.

   Parameters
   ----------
   mission_data : MissionData
       An instance of the MissionData class containing mission information.


   .. py:method:: convert_fli_df_to_ds() -> xarray.Dataset

      Convert the flight DataFrame to an xarray Dataset and store it in MissionData.

      Returns:
          xr.Dataset: The converted Dataset from the flight DataFrame.



   .. py:method:: format_flight_ds() -> xarray.Dataset

      Format the flight Dataset.

      Performs the following operations:
      - Sorts the Dataset based on present time
      - Drops the original time variable
      - Renames relevant variables

      Returns
      -------
      xr.Dataset
          The formatted flight Dataset.



   .. py:method:: load_flight()

      Load flight data from DBD files and preprocess the data.

      Loads and processes flight data through the following steps:
      - Loads data using the DBDReader package
      - Filters data within the mission start and end dates
      - Converts pressure from decibars to bars
      - Renames latitude and longitude columns for clarity



   .. py:method:: process_flight_data() -> xarray.Dataset

      Execute the complete flight data processing pipeline.

      Performs the following steps:
      1. Load flight data from DBD files
      2. Convert DataFrame to Dataset
      3. Add metadata attributes
      4. Format the Dataset

      Returns
      -------
      xr.Dataset
          The final processed flight Dataset.



   .. py:attribute:: mission_data
      :type:  glider_ingest.MissionData.MissionData


