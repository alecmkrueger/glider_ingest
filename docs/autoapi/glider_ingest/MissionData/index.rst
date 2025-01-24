glider_ingest.MissionData
=========================

.. py:module:: glider_ingest.MissionData


Classes
-------

.. autoapisummary::

   glider_ingest.MissionData.MissionData


Module Contents
---------------

.. py:class:: MissionData

   A class representing glider mission data and metadata.

   This class provides methods for managing and processing data
   related to a specific glider mission, including setup, 
   file location retrieval, metadata extraction, and NetCDF file generation.

   Attributes:
       memory_card_copy_loc (Path): Location of the copied memory card.
       working_dir (Path): Working directory for mission data processing.
       mission_num (str): Mission number identifier.
       glider_id (str): Identifier of the glider.
       nc_filename (str): NetCDF filename.
       output_nc_path (Path): Path for the output NetCDF file.
       mission_start_date (str | None): Start date of the mission.
       mission_end_date (str | None): End date of the mission.
       mission_year (str): Year of the mission.
       mission_title (str): Title of the mission.
       glider_name (str): Name of the glider.
       glider_ids (dict): Mapping of glider IDs to names.
       wmo_ids (dict): Mapping of glider IDs to WMO IDs.
       wmo_id (str): WMO ID for the glider.
       mission_vars (dict): Dictonary of mission variables.

   Post-Initialization Attributes:
       fli_files_loc (Path): Path to flight logs.
       fli_cache_loc (Path): Path to flight cache.
       sci_files_loc (Path): Path to science logs.
       sci_cache_loc (Path): Path to science cache.
       df_fli (pd.DataFrame): DataFrame for flight data.
       ds_fli (xr.Dataset): Dataset for flight data.
       df_sci (pd.DataFrame): DataFrame for science data.
       ds_sci (xr.Dataset): Dataset for science data.
       ds_mission (xr.Dataset): Combined dataset for mission data.


   .. py:method:: __attrs_post_init__()

      Post-initialization method to set up file locations for the mission data.

      This method is called automatically after the object is initialized to define paths for
      flight card logs, science card logs, and their respective caches.



   .. py:method:: _extract_full_filename(file)

      Extracts the full filename from a given file based on specific content.

      Args:
          file (str): Path to the file to read.

      Returns:
          str: The extracted full filename, or None if not found.



   .. py:method:: _get_sample_file()

      Retrieves a sample file from the science card files directory.

      Returns:
          str: A path to a sample file from the science card directory.



   .. py:method:: _parse_and_validate_glider_name(name)

      Parses and validates the glider name from the mission file name.

      Args:
          name (str): The full filename string.

      Raises:
          ValueError: If the glider name is not found or is invalid.



   .. py:method:: _parse_mission_year(name)

      Parses the mission year from the full filename.

      Args:
          name (str): The full filename string.



   .. py:method:: add_attrs()

      Adds flight, science, and mission attributes to the dataset.



   .. py:method:: add_global_attrs()


   .. py:method:: add_variables(variables: list[glider_ingest.variable.Variable])

      Adds variables to the mission data.

      Args:
          variables (list): list of Variable objects to add to the mission data.



   .. py:method:: get_file_locs()

      Defines and sets the file locations for flight card and science card data, including caches.

      This method checks for case-insensitivity in file path locations to ensure proper retrieval
      of files, whether the case is uppercase or lowercase.



   .. py:method:: get_files(files_loc: pathlib.Path, extension: str)


   .. py:method:: get_mission_date_range()

      Sets the mission start and end dates if not provided. Default start date is '2010-01-01' and
      the end date is set to one year after the current date.

      This method ensures that if the mission dates are not provided, reasonable defaults are applied.



   .. py:method:: get_mission_title()

      Sets the mission title if not provided. Defaults to 'Mission {mission_num}'.

      This method ensures that if the mission title is not specified, a default title is generated
      using the mission number.



   .. py:method:: get_mission_year_and_glider()

      Extracts the mission year and glider details from a sample file.

      This method identifies the year of the mission from the file name and validates the glider's name
      or ID against a predefined list of possible values.



   .. py:method:: get_nc_filename()

      Generates the NetCDF filename based on the mission number, year, and glider ID.

      This method ensures that a valid filename is created if not provided.



   .. py:method:: get_output_nc_path()

      Determines the output NetCDF file path based on the working directory and mission title.

      This method ensures that the directory exists and the file path is set up correctly.



   .. py:method:: get_wmo_id()

      Retrieves the WMO identifier for the glider based on its ID.

      If the WMO ID is not provided, it looks up the value from the `wmo_ids` dictionary.



   .. py:method:: init_base_variables()

      Initializes the base variables.



   .. py:method:: setup()

      Initializes the mission data by setting up necessary attributes like mission date range,
      year, glider information, WMO ID, mission title, and NetCDF filename.

      This method should be called after initialization to configure the mission object fully.



   .. py:attribute:: df_fli
      :type:  pandas.DataFrame


   .. py:attribute:: df_sci
      :type:  pandas.DataFrame


   .. py:attribute:: ds_fli
      :type:  xarray.Dataset


   .. py:attribute:: ds_mission
      :type:  xarray.Dataset


   .. py:attribute:: ds_sci
      :type:  xarray.Dataset


   .. py:attribute:: fli_cache_loc
      :type:  pathlib.Path


   .. py:attribute:: fli_files_loc
      :type:  pathlib.Path


   .. py:attribute:: glider_id
      :type:  str


   .. py:attribute:: glider_ids
      :type:  dict


   .. py:attribute:: glider_name
      :type:  str


   .. py:attribute:: memory_card_copy_loc
      :type:  pathlib.Path


   .. py:attribute:: mission_end_date
      :type:  str | None


   .. py:attribute:: mission_num
      :type:  str


   .. py:attribute:: mission_start_date
      :type:  str | None


   .. py:attribute:: mission_title
      :type:  str


   .. py:attribute:: mission_vars
      :type:  dict | None


   .. py:attribute:: mission_year
      :type:  str


   .. py:attribute:: nc_filename
      :type:  str


   .. py:attribute:: output_nc_path
      :type:  pathlib.Path


   .. py:attribute:: sci_cache_loc
      :type:  pathlib.Path


   .. py:attribute:: sci_files_loc
      :type:  pathlib.Path


   .. py:attribute:: wmo_id
      :type:  str


   .. py:attribute:: wmo_ids
      :type:  dict


   .. py:attribute:: working_dir
      :type:  pathlib.Path


