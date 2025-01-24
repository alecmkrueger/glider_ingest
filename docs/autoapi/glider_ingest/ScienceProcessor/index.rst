glider_ingest.ScienceProcessor
==============================

.. py:module:: glider_ingest.ScienceProcessor


Classes
-------

.. autoapisummary::

   glider_ingest.ScienceProcessor.ScienceProcessor


Module Contents
---------------

.. py:class:: ScienceProcessor

   A class to process science data from glider missions.

   This class handles the loading, processing, and conversion of science data
   from raw files into a structured dataset, while also performing variable
   calculations and renaming for consistency.

   Attributes
   ----------
   mission_data : MissionData
       An instance of the MissionData class containing mission-related configurations and data storage.


   .. py:method:: convert_sci_df_to_ds() -> xarray.Dataset

      Convert the processed science DataFrame to an xarray Dataset.

      This method adds platform metadata and converts the science DataFrame into a structured xarray Dataset.

      Returns
      -------
      xr.Dataset
          The science dataset with platform metadata added.



   .. py:method:: filter_sci_vars(variables: list)

      Determine the subset of science variables to process based on their presence.

      Parameters
      ----------
      variables : list
          A list of available science variables from the mission data.

      Returns
      -------
      list
          A list of science variables that are present and should be processed.



   .. py:method:: format_sci_ds() -> xarray.Dataset

      Format the science dataset by sorting and renaming variables.

      This method organizes variables and renames them for consistency with the mission dataset's standards.

      Returns
      -------
      xr.Dataset
          The formatted science dataset.



   .. py:method:: load_science()

      Load and process science data from raw mission files.

      This method reads raw science data files, filters relevant variables,
      and computes derived quantities like salinity and density.

      Returns
      -------
      pd.DataFrame
          A DataFrame containing processed science data.



   .. py:method:: process_sci_data() -> xarray.Dataset

      Perform all processing steps for science data.

      This method processes the science data from raw files to a formatted xarray Dataset,
      including variable calculations and formatting.

      Returns
      -------
      xr.Dataset
          The processed and formatted science dataset.



   .. py:attribute:: mission_data
      :type:  glider_ingest.MissionData.MissionData


