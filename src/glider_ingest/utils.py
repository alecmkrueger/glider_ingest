"""
Module containing utility functions for the package.
"""

# Import Packages
import numpy as np
import xarray as xr
import datetime
from functools import wraps
from time import time
import inspect

def print_time(message: str) -> None:
    """
    Print a message with the current time appended.

    Parameters
    ----------
    message : str
        The message to print.

    Notes
    -----
    The current time is formatted as 'HH:MM:SS'.
    """
    # Get current time
    current_time = datetime.datetime.today().strftime('%H:%M:%S')
    # Combine the message with the time
    whole_message = f'{message}: {current_time}'
    # Print the final message
    print(whole_message)
    

def f_print(*args, return_string=False):
    # Get the current frame and extract the calling frame
    frame = inspect.currentframe().f_back
    # Combine locals and globals for name lookup
    all_vars = {**frame.f_globals, **frame.f_locals}
    
    results = []
    for var in args:
        # Find all variable names that match the value of `var`
        var_names = [name for name, val in all_vars.items() if val is var]
        if var_names:
            # Use the first matching variable name
            results.append(f"{var_names[0]} = {var}")
        else:
            results.append(f"Could not determine variable name for value: {var}")
    
    # Return or print the result
    if return_string:
        return ", ".join(results)
    else:
        print(", ".join(results))

print(f_print(1,return_string=True))

def timing(f):
    """Time a function.

    Args:
        f (function): function to time

    Returns:
        wrapper: prints the time it took to run the function
    """
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('func:%r args:[%r, %r] took: %2.4f sec' % \
          (f.__name__, args, kw, te-ts))
        return result
    return wrap

def find_nth(haystack: str, needle: str, n: int) -> int:
    """
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
    """
    # Start at the first occurrence of the substring
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        # Find the next occurrence
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start

def invert_dict(dict: dict) -> dict:
    """
    Invert the keys and values of a dictionary.

    Parameters
    ----------
    dict : dict
        The dictionary to invert.

    Returns
    -------
    dict
        A new dictionary with keys and values swapped.
    """
    # Create a new dictionary with inverted key-value pairs
    return {value: key for key, value in dict.items()}

def get_polygon_coords(ds_mission: xr.Dataset) -> str:
    """
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
    """
    # Get the maximum latitude below 29.5
    lat_max = np.nanmax(ds_mission.latitude[np.where(ds_mission.latitude.values < 29.5)].values)
    # Get the minimum latitude below 29.5
    lat_min = np.nanmin(ds_mission.latitude[np.where(ds_mission.latitude.values < 29.5)].values)
    # Get the maximum longitude
    lon_max = np.nanmax(ds_mission.longitude.values)
    # Get the minimum longitude
    lon_min = np.nanmin(ds_mission.longitude.values)

    # Construct polygon points
    polygon_1 = f"{lat_max} {ds_mission.longitude[np.where(ds_mission.latitude == lat_max)[0][0]].values}"  # Northmost
    polygon_2 = f"{ds_mission.latitude[np.where(ds_mission.longitude == lon_max)[0][0]].values} {lon_max}"  # Eastmost
    polygon_3 = f"{lat_min} {ds_mission.longitude[np.where(ds_mission.latitude == lat_min)[0][0]].values}"  # Southmost
    polygon_4 = f"{ds_mission.latitude[np.where(ds_mission.longitude == lon_min)[0][0]].values} {lon_min}"  # Westmost
    polygon_5 = polygon_1  # Close the polygon

    # Combine points into WKT polygon format
    return f"POLYGON (({polygon_1}, {polygon_2}, {polygon_3}, {polygon_4}, {polygon_5}))"

def get_wmo_id(glider_id: str) -> str:
    """
    Extract the WMO ID from a glider ID.
    """
    if isinstance(glider_id, int):
        glider_id = str(glider_id)
    glider_ids = {'199': 'Dora', '307': 'Reveille', '308': 'Howdy', '540': 'Stommel', '541': 'Sverdrup', '1148': 'unit_1148'}
    wmo_ids = {'199': 'unknown', '307': '4801938', '308': '4801915', '540': '4801916', '541': '4801924', '1148': '4801915'}
    return wmo_ids[glider_id]
