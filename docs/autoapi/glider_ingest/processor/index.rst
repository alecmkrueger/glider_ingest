glider_ingest.processor
=======================

.. py:module:: glider_ingest.processor


Classes
-------

.. autoapisummary::

   glider_ingest.processor.Processor


Module Contents
---------------

.. py:class:: Processor

   A class to process glider data


   .. py:method:: add_mission_vars(mission_vars: list[glider_ingest.variable.Variable] | list[str] | glider_ingest.variable.Variable | str)

      Add variables to the mission_vars list.

      :param mission_vars: Can be any of:
      :param - Single Variable object:
      :param - Single string:
      :param - List of Variable objects:
      :param - List of strings:
      :param - Mixed list of Variables and strings:



   .. py:method:: process(return_ds=True)


   .. py:method:: remove_mission_vars(vars_to_remove: list[str] | str)

      Remove variables from mission_vars list by data source name.

      :param vars_to_remove: Can be a single string or list of strings representing
                             data_source_names to remove



   .. py:method:: save(save_path=None)


   .. py:attribute:: dbd
      :type:  dbdreader.MultiDBD | None


   .. py:property:: dbd_variables
      :type: list



   .. py:property:: df
      :type: pandas.DataFrame



   .. py:attribute:: ds
      :type:  xarray.Dataset | None


   .. py:property:: eng_dbd_vars
      :type: list


      Get the engineering DBD variables.


   .. py:property:: eng_df
      :type: pandas.DataFrame



   .. py:property:: eng_ds
      :type: xarray.Dataset



   .. py:property:: eng_vars
      :type: list


      Get engineering variables (non-calculated vars starting with ``m_``)


   .. py:property:: glider_id
      :type: str | None


      Get the glider ID.


   .. py:attribute:: glider_ids
      :type:  dict


   .. py:property:: glider_name
      :type: str | None


      Get the glider name.


   .. py:attribute:: include_gridded_data
      :type:  bool


   .. py:property:: log_level
      :type: str


      Get the current logging level.


   .. py:property:: logger
      :type: logging.Logger


      Get the logger instance for this processor.


   .. py:attribute:: memory_card_copy_path
      :type:  pathlib.Path


   .. py:attribute:: mission_end_date
      :type:  datetime.datetime


   .. py:property:: mission_folder_name
      :type: str


      Get the mission folder name.


   .. py:property:: mission_folder_path
      :type: pathlib.Path


      Get the mission folder path.


   .. py:attribute:: mission_num
      :type:  str


   .. py:attribute:: mission_start_date
      :type:  datetime.datetime


   .. py:property:: mission_title
      :type: str


      Get the mission title.


   .. py:attribute:: mission_vars
      :type:  list[glider_ingest.variable.Variable]


   .. py:property:: mission_year
      :type: str


      Get the mission year.


   .. py:property:: netcdf_filename
      :type: str


      Get the NetCDF filename.


   .. py:property:: netcdf_output_path
      :type: pathlib.Path


      Get the NetCDF path.


   .. py:attribute:: recopy_files
      :type:  bool


   .. py:property:: sci_dbd_vars
      :type: list


      Get the science DBD variables.


   .. py:property:: sci_df
      :type: pandas.DataFrame



   .. py:property:: sci_ds
      :type: xarray.Dataset



   .. py:property:: sci_vars
      :type: list


      Get science variables (all non-engineering variables)


   .. py:property:: wmo_id
      :type: str | None


      Get the WMO ID.


   .. py:attribute:: wmo_ids
      :type:  dict


   .. py:attribute:: working_dir
      :type:  pathlib.Path


