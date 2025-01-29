glider_ingest.processor
=======================

.. py:module:: glider_ingest.processor


Attributes
----------

.. autoapisummary::

   glider_ingest.processor.ds
   glider_ingest.processor.memory_card_copy_path
   glider_ingest.processor.processor
   glider_ingest.processor.working_dir


Classes
-------

.. autoapisummary::

   glider_ingest.processor.Processor


Module Contents
---------------

.. py:class:: Processor

   A class to process glider data


   .. py:method:: __attrs_post_init__()

      Post init method to add default variables to the mission_vars list



   .. py:method:: _add_attrs()


   .. py:method:: _add_global_attrs()


   .. py:method:: _add_gridded_data()

      Add gridded data to the dataset, must be called after adding attrs



   .. py:method:: _add_variable_attrs()


   .. py:method:: _calculate_vars(df)


   .. py:method:: _check_default_variables(dbd, variables_to_get: list)

      Check that the default variables are in the dbd variables



   .. py:method:: _check_mission_var_duplicates()

      Check for duplicate variables in the mission_vars list



   .. py:method:: _convert_dbd_to_dataframe()

      Get the dbd data as a dataframe



   .. py:method:: _convert_df_to_ds()


   .. py:method:: _copy_cache_files()

      Move the cache files to the working directory



   .. py:method:: _copy_files()

      Copy only LOGS and STATE/CACHE folders from memory card copy to working directory



   .. py:method:: _format_time(df: pandas.DataFrame)


   .. py:method:: _get_cache_files(as_string: bool = False)

      Get the cache files from the memory card copy



   .. py:method:: _get_cache_files_path()

      Get the cache file path from the memory card copy



   .. py:method:: _get_dbd_data()


   .. py:method:: _get_dbd_files(as_string=False)

      Get the dbd files from the memory card copy



   .. py:method:: _get_dbd_variables(dbd) -> list

      Get the dbd variables from the files. Returns both sci and eng if both are true.

      If sci_vars and eng_vars are both False, raise a ValueError


      Parameters
      ----------
      sci_vars : bool, optional
      Whether to include science variables, default: True
      eng_vars : bool, optional
      Whether to include engineering variables, default: True

      Returns
      -------
      list

      Raises
      ------
      ValueError
      If sci_vars and eng_vars are both False



   .. py:method:: _get_depth()


   .. py:method:: _get_files_by_extension(directory_path: pathlib.Path, extensions: list[str], as_string: bool = False) -> list

      Get files from a directory with specified extensions.

      Args:
          directory_path (Path): Directory to search for files
          extensions (list[str]): List of file extensions to match (e.g. ['.dbd', '.DBD'])
          as_string (bool): Whether to return paths as strings

      Returns:
          list: List of matching files as Path objects or strings



   .. py:method:: _get_full_filename()

      Get the full filename from the file
      Args:
          file (str): Path to the file to read.

      Returns:
          str: The extracted full filename, or None if not found.



   .. py:method:: _get_glider_id()

      Get the glider id from the filename.

      Extracts and validates the glider identifier from the filename, converting between
      glider names and IDs as needed using the glider_ids mapping.

      Returns
      -------
      str
          The validated glider ID



   .. py:method:: _get_latitude()


   .. py:method:: _get_longitude()


   .. py:method:: _get_mission_variable_data_source_names(filter_out_none=False)

      Get the mission variable data source names from the mission_vars list



   .. py:method:: _get_mission_variable_short_names(filter_out_none=False)

      Get the mission variable data source names from the mission_vars list



   .. py:method:: _get_mission_variables(filter_out_none=False)

      Get the mission variables from the mission_vars list. Filter out None data_source_name values if desired.



   .. py:method:: _get_mission_year()

      Get the mission year from the filename.

      Extracts and validates the mission year from the filename, converting between
      mission names and IDs as needed using the mission_ids mapping.

      Returns
      -------
      str
          The validated mission year



   .. py:method:: _get_random_sci_file()

      Get a random sci file from the mission folder



   .. py:method:: _get_sci_files()

      Get the sci files from the memory card copy



   .. py:method:: _get_time()


   .. py:method:: _read_dbd()

      Read the files from the memory card copy



   .. py:method:: _update_dataframe_columns(df)

      Update the dataframe columns with the mission variables.
      Adjusting the current column names, which are data source names, to their short_name values.



   .. py:method:: add_mission_vars(mission_vars: list[glider_ingest.variable.Variable])

      Add a variable to the mission_vars list



   .. py:method:: process(return_ds=True)


   .. py:method:: save(save_path=None)


   .. py:attribute:: _glider_id
      :type:  str


   .. py:attribute:: _glider_name
      :type:  str


   .. py:attribute:: _mission_folder_name
      :type:  str


   .. py:attribute:: _mission_folder_path
      :type:  pathlib.Path


   .. py:attribute:: _mission_title
      :type:  str


   .. py:attribute:: _mission_year
      :type:  str


   .. py:attribute:: _netcdf_filename
      :type:  str


   .. py:attribute:: _netcdf_output_path
      :type:  pathlib.Path


   .. py:attribute:: _wmo_id
      :type:  str


   .. py:attribute:: df
      :type:  pandas.DataFrame


   .. py:attribute:: ds
      :type:  xarray.Dataset


   .. py:property:: glider_id

      Get the glider ID.



   .. py:attribute:: glider_ids
      :type:  dict


   .. py:property:: glider_name

      Get the glider name.



   .. py:attribute:: memory_card_copy_path
      :type:  pathlib.Path


   .. py:attribute:: mission_end_date
      :type:  datetime.datetime


   .. py:property:: mission_folder_name

      Get the mission folder name.



   .. py:property:: mission_folder_path

      Get the mission folder path.



   .. py:attribute:: mission_num
      :type:  str


   .. py:attribute:: mission_start_date
      :type:  datetime.datetime


   .. py:property:: mission_title

      Get the mission title.



   .. py:attribute:: mission_vars
      :type:  list[glider_ingest.variable.Variable]


   .. py:property:: mission_year

      Get the mission year.



   .. py:property:: netcdf_filename

      Get the NetCDF filename.



   .. py:property:: netcdf_output_path

      Get the NetCDF path.



   .. py:property:: wmo_id

      Get the WMO ID.



   .. py:attribute:: wmo_ids
      :type:  dict


   .. py:attribute:: working_dir
      :type:  pathlib.Path


.. py:data:: ds

.. py:data:: memory_card_copy_path

.. py:data:: processor

.. py:data:: working_dir

