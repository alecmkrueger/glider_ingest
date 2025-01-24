glider_ingest.MissionProcessor
==============================

.. py:module:: glider_ingest.MissionProcessor


Classes
-------

.. autoapisummary::

   glider_ingest.MissionProcessor.MissionProcessor


Module Contents
---------------

.. py:class:: MissionProcessor

   A class to process and manage mission data for glider operations.

   This class integrates data from science and flight logs, combines them
   into a mission dataset, and saves the processed data to a NetCDF file.

   Attributes
   ----------
   mission_data : MissionData
       An instance of the MissionData class containing mission-related configurations and paths.


   .. py:method:: generate_mission_dataset()

      Generate the mission dataset by combining science and flight data.

      This method performs the following steps:
      1. Sets up mission metadata.
      2. Processes science and flight data.
      3. Combines science and flight datasets into a mission dataset.
      4. Adds gridded data and global attributes to the mission dataset.

      Raises
      ------
      AttributeError
          If `self.mission_data` does not contain the necessary data for processing.



   .. py:method:: process_fli()

      Process flight data for the mission.

      This method initializes a FlightProcessor, processes the flight data,
      and updates the mission data with the processed results.

      Returns
      -------
      MissionData
          Updated mission data after processing flight data.



   .. py:method:: process_sci()

      Process science data for the mission.

      This method initializes a ScienceProcessor, processes the science data,
      and updates the mission data with the processed results.

      Returns
      -------
      MissionData
          Updated mission data after processing science data.



   .. py:method:: save_mission_dataset()

      Save the mission dataset to a NetCDF file.

      This method generates the mission dataset if it has not already been created
      and saves the dataset to the configured output NetCDF file.

      Raises
      ------
      AttributeError
          If `self.mission_data` does not contain a mission dataset to save.



   .. py:attribute:: mission_data
      :type:  glider_ingest.MissionData.MissionData


