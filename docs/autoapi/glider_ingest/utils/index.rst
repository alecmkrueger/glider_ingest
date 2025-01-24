glider_ingest.utils
===================

.. py:module:: glider_ingest.utils

.. autoapi-nested-parse::

   Module containing utility functions for the package.



Functions
---------

.. autoapisummary::

   glider_ingest.utils.add_gridded_data
   glider_ingest.utils.find_nth
   glider_ingest.utils.get_polygon_coords
   glider_ingest.utils.get_wmo_id
   glider_ingest.utils.invert_dict
   glider_ingest.utils.print_time
   glider_ingest.utils.timing


Module Contents
---------------

.. py:function:: add_gridded_data(ds_mission: xarray.Dataset) -> xarray.Dataset

   Add gridded data to a mission dataset using the Gridder class.

   Parameters
   ----------
   ds_mission : xarray.Dataset
       The mission dataset to process.

   Returns
   -------
   xarray.Dataset
       The updated dataset with gridded data added.

   Notes
   -----
   This function creates a `Gridder` object to compute the gridded dataset,
   updates the mission dataset with the gridded data, and prints timing information.


.. py:function:: find_nth(haystack: str, needle: str, n: int) -> int

   Find the nth occurrence of a substring in a string.

   Parameters
   ----------
   haystack : str
       The string to search in.
   needle : str
       The substring to find.
   n : int
       The occurrence number of the substring to find.

   Returns
   -------
   int
       The index of the nth occurrence of the substring, or -1 if not found.


.. py:function:: get_polygon_coords(ds_mission: xarray.Dataset) -> str

   Generate polygon coordinates for the dataset's global attributes.

   Parameters
   ----------
   ds_mission : xarray.Dataset
       The mission dataset containing latitude and longitude values.

   Returns
   -------
   str
       A string representation of the polygon in Well-Known Text (WKT) format.

   Notes
   -----
   The polygon is constructed based on the northmost, eastmost, southmost, 
   and westmost points where latitude is below 29.5.


.. py:function:: get_wmo_id(glider_id: str) -> str

   Extract the WMO ID from a glider ID.


.. py:function:: invert_dict(dict: invert_dict.dict) -> invert_dict.dict

   Invert the keys and values of a dictionary.

   Parameters
   ----------
   dict : dict
       The dictionary to invert.

   Returns
   -------
   dict
       A new dictionary with keys and values swapped.


.. py:function:: print_time(message: str) -> None

   Print a message with the current time appended.

   Parameters
   ----------
   message : str
       The message to print.

   Notes
   -----
   The current time is formatted as 'HH:MM:SS'.


.. py:function:: timing(f)

   Time a function.

   Args:
       f (function): function to time

   Returns:
       wrapper: prints the time it took to run the function


