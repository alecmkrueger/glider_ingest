glider_ingest.utils
===================

.. py:module:: glider_ingest.utils

.. autoapi-nested-parse::

   Module containing utility functions for the package.





Module Contents
---------------

.. py:function:: f_print(*args, return_string=False)

.. py:function:: find_nth(haystack: str, needle: str, n: int) -> int

   Find the nth occurrence of a substring in a string.

   :param haystack: The string to search in.
   :type haystack: str
   :param needle: The substring to find.
   :type needle: str
   :param n: The occurrence number of the substring to find.
   :type n: int

   :returns: The index of the nth occurrence of the substring, or -1 if not found.
   :rtype: int


.. py:function:: get_polygon_bounds(longitude: numpy.ndarray, latitude: numpy.ndarray) -> list

   Generate polygon coordinates for the dataset's global attributes.


.. py:function:: get_polygon_coords(longitude: numpy.ndarray, latitude: numpy.ndarray, lat_max: float, lat_min: float, lon_max: float, lon_min: float) -> str

   Generate polygon coordinates for the dataset's global attributes.

   :param ds_mission: The mission dataset containing latitude and longitude values.
   :type ds_mission: xarray.Dataset

   :returns: A string representation of the polygon in Well-Known Text (WKT) format.
   :rtype: str

   .. rubric:: Notes

   The polygon is constructed based on the northmost, eastmost, southmost,
   and westmost points where latitude is below 29.5.


.. py:function:: get_wmo_id(glider_id: str | int) -> str

   Extract the WMO ID from a glider ID.


.. py:function:: invert_dict(dict: invert_dict.dict) -> invert_dict.dict

   Invert the keys and values of a dictionary.

   :param dict: The dictionary to invert.
   :type dict: dict

   :returns: A new dictionary with keys and values swapped.
   :rtype: dict


.. py:function:: print_time(message: str) -> None

   Print a message with the current time appended.

   :param message: The message to print.
   :type message: str

   .. rubric:: Notes

   The current time is formatted as 'HH:MM:SS'.


.. py:function:: setup_logging(level: str = 'INFO') -> None

   Configure logging for the package. With specific name and format.

   :param level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL), by default 'INFO'
   :type level: str, optional


.. py:function:: timing(f)

   Time a function.

   :param f: function to time
   :type f: function

   :returns: prints the time it took to run the function
   :rtype: wrapper


