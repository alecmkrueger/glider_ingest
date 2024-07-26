# utils.py

# Import Packages
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
import datetime
import shutil
import subprocess
import os
import gsw
import multiprocessing
import uuid
from attrs import define,field
from concurrent.futures import ThreadPoolExecutor, as_completed

# AUTHORS:
# Sakib Mahmud, Texas A&M University, Geochemical and Environmental Research Group, sakib@tamu.edu
# Xiao Ge, Texas A&M University, Geochemical and Environmental Research Group, gexiao@tamu.edu
# Alec Krueger, Texas A&M University, Geochemical and Environmental Research Group, alecmkrueger@tamu.edu


# Define functions and classes

def print_time(message):
    # Get current time
    current_time = datetime.datetime.today().strftime('%H:%M:%S')
    # Add time to message
    whole_message = f'{message}: {current_time}'
    # Print out the message
    print(whole_message)

def delete_files_in_directory(directory:Path):
    # Check if the user wishes to delete all files in the directory
    confirmation = input(f"Are you sure you want to delete all files in '{directory}' and its subdirectories? Type 'yes' to confirm, 'no' to continue without deleting files, press escape to cancel and end ")
    # If so then begin finding files
    if confirmation.lower() == 'yes':
        # clear cache
        cache_path = directory.parent.joinpath('cache')
        [os.remove(file) for file in cache_path.rglob('*.CAC')]
        # clear all files in the given directory
        for root, _, files in os.walk(directory):
            file_count = len(files)
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
            if file_count > 0:
                print(f"Cleaned {root}, deleted {file_count} file(s).")
        print_time("All files have been deleted")
    elif confirmation.lower() == 'no':
        print_time('Continuing without deleting files, this may cause unexpected behaviours including data duplication')
    else:
        raise ValueError("Cancelling: If you did not press escape, ensure you type 'yes' or 'no'. ")



def create_directory(data_dir:Path|None=None):
    if data_dir is None:
        data_dir = Path('data')
    # Create cache dir
    cache_path = data_dir.parent.joinpath('cache')
    cache_path.mkdir(exist_ok=True)
    # Define the two data type folders
    data_types = ['processed','raw_copy']
    # Define the three processed folders
    processed_data_types = ['Flight','nc','Science']
    # Define the raw data type folders by the file extension of the files to be stored
    raw_flight_extensions = ["DBD", "MBD", "SBD", "MLG"]
    raw_science_extensions = ["EBD", "NLG", "TBD", "NBD"]
    # Loop through the two data type folders
    for dtype in data_types:
        if dtype == 'processed':
            for processed_dtype in processed_data_types:
                # Example directory being created: data_dir/processed/Flight
                os.makedirs(data_dir.joinpath(dtype, processed_dtype), exist_ok=True)
        elif dtype == 'raw_copy':
            # Package Flight and Science with their respective data type folders (extensions)
            for data_source,extensions in zip(['Flight','Science'],[raw_flight_extensions,raw_science_extensions]):
                for extension in extensions:
                    # Example directory being created: data_dir/raw_copy/Flight/DBD
                    os.makedirs(data_dir.joinpath(dtype ,data_source, extension), exist_ok=True)

def copy_file(input_file_path, output_file_path):
    shutil.copy2(input_file_path, output_file_path)

def copy_raw_data(input_data_dir: Path, working_directory: Path, max_workers: int|None = None):
    '''
    Copy data from the memory card to the working directory using multithreading.
    This will also create the folders to hold the data if they do not exist yet.

    input_data_dir (pathlib.Path): Object that points to the memory card from the buoy
    working_directory (pathlib.Path): Object that points to where we want the copies to go
    max_workers (int): Maximum number of threads to use for parallel processing. Defaults to the number of CPU cores.
    '''
    print_time('Copying Raw files')
    if max_workers is None:
        max_workers = multiprocessing.cpu_count()
    
    raw_output_data_dir = working_directory.joinpath('raw_copy')
    
    tasks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for data_source, extensions in zip(['Flight', 'Science'], [["DBD", "MBD", "SBD", "MLG", "CAC"], ["EBD", "NLG", "TBD", "NBD", "CAC"]]):
            input_data_path = input_data_dir.joinpath(f'{data_source}_card')
            for file_extension in extensions:
                # If the extension is CAC then we want to copy the files to the cache folder
                if file_extension == 'CAC':
                    output_data_path = working_directory.parent.joinpath('cache')
                else:
                    output_data_path = raw_output_data_dir.joinpath(data_source, file_extension)
                # Ensure that the directory exists (it should if the user ran the create_directory function before running this (copy_raw_data)
                output_data_path.mkdir(parents=True, exist_ok=True)
                # Find all of the files with the file extension 
                input_files = input_data_path.rglob(f'*.{file_extension}')
                # Loop through the files with matching extensions
                for input_file_path in input_files:
                    # Define where the file will be placed
                    output_file_path = output_data_path.joinpath(input_file_path.name)
                    # Append the input and output file paths to a list
                    tasks.append((input_file_path, output_file_path))
        # Queue the copy_file function using multiprocessing on the input and output file paths
        futures = [executor.submit(copy_file, input_file_path, output_file_path) for input_file_path, output_file_path in tasks]
        # Perform the multiprocessing
        for future in as_completed(futures):
            try:
                future.result()  # Raise any exceptions that occurred
            except Exception as e:
                print(f"Error copying file: {e}")
    
    print_time('Done Copying Raw files')

def rename_file(rename_dbd_files_path, file):
    subprocess.run([rename_dbd_files_path, file])

def rename_dbd_ebd_files(working_directory: Path, max_workers: int = None):
    '''
    Rename files with extensions of DBD or EBD to contain date and glider name in the input data directory
    using multithreading.

    working_directory (pathlib.Path): Object that points to the folder that contains the files to be renamed
    max_workers (int): Maximum number of threads to use for parallel processing. Defaults to number of CPU cores.
    '''
    print_time('Renaming dbd files')

    if max_workers is None:
        max_workers = multiprocessing.cpu_count()
    
    working_directory = working_directory.joinpath('raw_copy')
    extensions = ['DBD', 'EBD']
    rename_dbd_files_path = Path('rename_dbd_files').resolve()

    tasks = []
    for extension in extensions:
        data_files = working_directory.rglob(f'*.{extension}')
        for file in data_files:
            tasks.append(file)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(rename_file, rename_dbd_files_path, file) for file in tasks]
        
        for future in as_completed(futures):
            try:
                future.result()  # Raise any exceptions that occurred
            except Exception as e:
                print(f"Error renaming file: {e}")

    print_time("Done renaming dbd files")

def convert_file(dbd2asc_path, raw_file, ascii_file):
    cmd = f'{dbd2asc_path} "{raw_file}" > "{ascii_file}"'
    os.system(cmd)

def convert_dbd_ebd_to_ascii(working_directory: Path, system: str = 'windows', max_workers: int = 4):
    '''
    Converts all DBD and EBD files to ascii in the input directory and saves them to the output directory

    working_directory (pathlib.Path): Object that points to the files to convert
    ouput_data_dir (pathlib.Path): Object that points to where the files are to be saved to
    max_workers (int): The maximum number of threads to use for parallel processing
    '''
    print_time('Converting to ascii')
    output_data_dir = working_directory.joinpath('processed')
    working_directory = working_directory.joinpath('raw_copy')
    
    # Define the Path object for where the dbd2asc executable is
    dbd2asc_path = Path('dbd2asc').resolve()
    
    # Define the data_sources
    data_sources = ['Flight', 'Science']
    # Define the extensions for the data sources
    extensions = ['DBD', 'EBD']
    
    # Collect all files to be processed
    tasks = []
    for data_source, extension in zip(data_sources, extensions):
        raw_files = working_directory.joinpath(data_source).joinpath(extension).rglob('*')
        for raw_file in raw_files:
            ascii_file = output_data_dir.joinpath(data_source, f'{raw_file.name}.asc')
            tasks.append((dbd2asc_path, raw_file, ascii_file))
    
    # Process files in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(convert_file, dbd2asc_path, raw_file, ascii_file) for dbd2asc_path, raw_file, ascii_file in tasks]
        for future in as_completed(futures):
            future.result()  # Raise any exceptions that occurred
    
    print_time('Done Converting to ascii')

def read_sci_file(file:Path) -> pd.DataFrame:
    '''
    Tries to read a file from science and filters to select a few variables
    '''
    try:
        # Read in the data
        df_raw = pd.read_csv(file, header=14, sep=' ', skiprows=[15,16])

        # Check if there are enough lines to read the file if there are not then return None,
        # any Nones are handled by the pd.concat function in join_ascii_files
        if len(df_raw)<3:
            return None
        
        else:
            variables = df_raw.keys()
            # Define subsets of columns based on the presence of sci_oxy4_oxygen and sci_flbbcd_bb_units
            if 'sci_oxy4_oxygen' in variables and 'sci_flbbcd_bb_units' in variables:
                 present_variables = ['sci_m_present_time', 'sci_flbbcd_bb_units', 'sci_flbbcd_cdom_units', 'sci_flbbcd_chlor_units', 'sci_water_pressure', 'sci_water_temp', 'sci_water_cond', 'sci_oxy4_oxygen']

            elif 'sci_oxy4_oxygen' in variables and 'sci_flbbcd_bb_units' not in variables:
                 present_variables = ['sci_m_present_time', 'sci_water_pressure', 'sci_water_temp', 'sci_water_cond', 'sci_oxy4_oxygen']

            elif 'sci_oxy4_oxygen' not in variables and 'sci_flbbcd_bb_units' in variables:
                 present_variables = ['sci_m_present_time', 'sci_flbbcd_bb_units', 'sci_flbbcd_cdom_units', 'sci_flbbcd_chlor_units', 'sci_water_pressure', 'sci_water_temp', 'sci_water_cond']

            elif 'sci_oxy4_oxygen' not in variables and 'sci_flbbcd_bb_units' not in variables:
                 present_variables = ['sci_m_present_time', 'sci_water_pressure', 'sci_water_temp', 'sci_water_cond']

            df_filtered = df_raw[present_variables]
            # Parse the timestamp explicitly
            dates = df_filtered['sci_m_present_time'].copy()

            dates_datetime =  pd.to_datetime(dates, unit='s', errors='coerce')
            # df_filtered.loc[:, 'sci_m_present_time'] = dates_datetime
            df_filtered = df_filtered.assign(sci_m_present_time=dates_datetime)

    except Exception as e:
        print(f'Unable to read and skipping {file.stem}: {e}')
        return None
    
    return df_filtered

def read_flight_file(file:Path) -> pd.DataFrame:
    '''
    Tries to read flight data and filteres to select a few variables
    '''
    try:
        df_raw = pd.read_csv(file, header=14, sep=' ', skiprows=[15,16])

        # Check if there are enough lines to read the file if there are not then return None,
        # any Nones are handled by the pd.concat function in join_ascii_files
        if len(df_raw) < 3:
            return None
        else:
            present_variables = ['m_present_time','m_lat','m_lon','m_pressure','m_water_depth']
            df_filtered = df_raw[present_variables]
            # Parse the timestamp explicitly
            dates = df_filtered['m_present_time'].copy()
            dates_datetime =  pd.to_datetime(dates, unit='s', errors='coerce')
            df_filtered = df_filtered.assign(m_present_time=dates_datetime)
    except Exception as e:
        print(f'Unable to read and skipping {file.stem}: {e}')
        return None
    
    return df_filtered


def join_ascii_files(files, file_reader, max_workers=None) -> pd.DataFrame:
    '''
    Uses ThreadPoolExecutor to read all files using a file reader function then concatenates all the files.
    
    files (list): List of file paths to read.
    file_reader (function): Function to read a single file.
    max_workers (int): Maximum number of threads to use for parallel processing. Defaults to number of CPU cores.
    '''
    if max_workers is None:
        max_workers = multiprocessing.cpu_count()

    # Use ThreadPoolExecutor to read files in parallel
    df_list = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(file_reader, file): file for file in files}
        
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                df_list.append(future.result())
            except Exception as e:
                print(f"Error reading {file}: {e}")

    df_concat = pd.concat(df_list, axis=0)
    return df_concat

def process_sci_df(df:pd.DataFrame) -> pd.DataFrame:
    '''
    Process the data to filter and calculate salinity and density
    '''
    # Remove any data with erroneous dates (outside expected dates 2010-2030)
    df = df[(df['sci_m_present_time'] > '2010-01-01') & (df['sci_m_present_time'] < '2030-01-01')]
    # Convert pressure from db to dbar
    df['sci_water_pressure'] = df['sci_water_pressure'] * 10
    # Calculate salinity and density
    df['sci_water_sal'] = gsw.SP_from_C(df['sci_water_cond']*10,df['sci_water_temp'],df['sci_water_pressure'])
    CT = gsw.CT_from_t(df['sci_water_sal'],df['sci_water_temp'],df['sci_water_pressure'])
    df['sci_water_dens'] = gsw.rho_t_exact(df['sci_water_sal'],CT,df['sci_water_pressure'])
    return df

def convert_sci_df_to_ds(df:pd.DataFrame,glider_id:dict,glider:str) -> xr.Dataset:
    '''
    Convert the given science dataframe to a xarray dataset
    '''
    bds = xr.Dataset() # put the platform info into the dataset on the top
    bds['platform'] = xr.DataArray(glider_id[glider])
    ds = xr.Dataset.from_dataframe(df)
    ds = bds.update(ds)
    return ds

def add_sci_attrs(ds:xr.Dataset,glider_id,glider,wmo_id) -> xr.Dataset:
    '''
    Add attributes to the science dataset
    '''
    variables = list(ds.data_vars)
    # Define variable attributes
    ds['platform'].attrs = {'ancillary_variables': ' ',
    'comment': ' ',
    'id': glider_id[glider],
    'instruments': 'instrument_ctd',
    'long_name': 'Slocum Glider '+ glider_id[glider],
    'type': 'platform',
    'wmo_id': wmo_id[glider],
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
    ds['sci_water_pressure'].attrs = {'accuracy': 0.01,
    'ancillary_variables': ' ',
    'axis': 'Z',
    'bytes': 4,
    'comment': 'Alias for sci_water_pressure, multiplied by 10 to convert from bar to dbar',
    'instrument': 'instrument_ctd',
    'long_name': 'CTD Pressure',
    'observation_type': 'measured',
    'platform': 'platform',
    'positive': 'down',
    'precision': 0.01,
    'reference_datum': 'sea-surface',
    'resolution': 0.01,
    'source_sensor': 'sci_water_pressure',
    'standard_name': 'sea_water_pressure',
    'units': 'bar',
    'valid_max': 2000.0,
    'valid_min': 0.0,
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
    ds['sci_water_temp'].attrs = {'accuracy': 0.004,
    'ancillary_variables': ' ',
    'bytes': 4,
    'instrument': 'instrument_ctd',
    'long_name': 'Temperature',
    'observation_type': 'measured',
    'platform': 'platform',
    'precision': 0.001,
    'resolution': 0.001,
    'standard_name': 'sea_water_temperature',
    'units': 'Celsius',
    'valid_max': 40.0,
    'valid_min': -5.0,
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
    ds['sci_water_cond'].attrs = {'accuracy': 0.001,
    'ancillary_variables': ' ',
    'bytes': 4,
    'instrument': 'instrument_ctd',
    'long_name': 'sci_water_cond',
    'observation_type': 'measured',
    'platform': 'platform',
    'precision': 1e-05,
    'resolution': 1e-05,
    'standard_name': 'sea_water_electrical_conductivity',
    'units': 'S m-1',
    'valid_max': 10.0,
    'valid_min': 0.0,
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
    ds['sci_water_sal'].attrs = {'accuracy': ' ',
    'ancillary_variables': ' ',
    'instrument': 'instrument_ctd',
    'long_name': 'Salinity',
    'observation_type': 'calculated',
    'platform': 'platform',
    'precision': ' ',
    'resolution': ' ',
    'standard_name': 'sea_water_practical_salinity',
    'units': '1',
    'valid_max': 40.0,
    'valid_min': 0.0,
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
    ds['sci_water_dens'].attrs = {'accuracy': ' ',
    'ancillary_variables': ' ',
    'instrument': 'instrument_ctd',
    'long_name': 'Density',
    'observation_type': 'calculated',
    'platform': 'platform',
    'precision': ' ',
    'resolution': ' ',
    'standard_name': 'sea_water_density',
    'units': 'kg m-3',
    'valid_max': 1040.0,
    'valid_min': 1015.0,
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
    if 'sci_flbbcd_bb_units' in variables:
        ds['sci_flbbcd_bb_units'].attrs = {'long_name':'science turbidity', 'standard_name':'backscatter', 'units':'nodim'}
        ds['sci_flbbcd_bb_units'].attrs = {'accuracy': ' ',
        'ancillary_variables': ' ',
        'instrument': 'instrument_flbbcd',
        'long_name': 'Turbidity',
        'observation_type': 'calculated',
        'platform': 'platform',
        'precision': ' ',
        'resolution': ' ',
        'standard_name': 'sea_water_turbidity',
        'units': '1',
        'valid_max': 1.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # ds['sci_flbbcd_cdom_units'].attrs = {'long_name':'science cdom', 'standard_name':'cdom', 'units':'ppb'}
        ds['sci_flbbcd_cdom_units'].attrs = {'accuracy': ' ',
        'ancillary_variables': ' ',
        'instrument': 'instrument_flbbcd',
        'long_name': 'CDOM',
        'observation_type': 'calculated',
        'platform': 'platform',
        'precision': ' ',
        'resolution': ' ',
        'standard_name': 'concentration_of_colored_dissolved_organic_matter_in_sea_water',
        'units': 'ppb',
        'valid_max': 50.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        # ds['sci_flbbcd_chlor_units'].attrs = {'long_name':'science chlorophyll', 'standard_name':'chlorophyll', 'units':'\u03BCg/L'}
        ds['sci_flbbcd_chlor_units'].attrs = {'accuracy': ' ',
        'ancillary_variables': ' ',
        'instrument': 'instrument_flbbcd',
        'long_name': 'Chlorophyll_a',
        'observation_type': 'calculated',
        'platform': 'platform',
        'precision': ' ',
        'resolution': ' ',
        'standard_name': 'mass_concentration_of_chlorophyll_a_in_sea_water',
        'units': '\u03BCg/L',
        'valid_max': 10.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}

    if 'sci_oxy4_oxygen' in variables:
        # ds['sci_oxy4_oxygen'].attrs = {'long_name':'oxygen', 'standard_name':'oxygen', 'units':'\u03BCmol/kg'}
        ds['sci_oxy4_oxygen'].attrs = {'accuracy': ' ',
        'ancillary_variables': ' ',
        'instrument': 'instrument_ctd_modular_do_sensor',
        'long_name': 'oxygen',
        'observation_type': 'calculated',
        'platform': 'platform',
        'precision': ' ',
        'resolution': ' ',
        'standard_name': 'moles_of_oxygen_per_unit_mass_in_sea_water',
        'units': '\u03BCmol/kg',
        'valid_max': 500.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}

    return ds

def format_sci_ds(ds:xr.Dataset) -> xr.Dataset:
    '''
    Format the science dataset by sorting and renameing variables
    '''
    # ds = ds.rename({'index': 'sci_idx'})
    ds['index'] = np.sort(ds['sci_m_present_time'].values.astype('datetime64[s]'))
    ds = ds.drop_vars('sci_m_present_time')
    if 'sci_oxy4_oxygen' in ds.data_vars.keys():
        ds = ds.rename({'index': 'time','sci_water_pressure':'pressure','sci_water_temp':'temperature',
        'sci_water_cond':'conductivity','sci_water_sal':'salinity','sci_water_dens':'density','sci_flbbcd_bb_units':'turbidity',
        'sci_flbbcd_cdom_units':'cdom','sci_flbbcd_chlor_units':'chlorophyll','sci_oxy4_oxygen':'oxygen'})
    else:
        # ds = ds.rename({'index': 'time','sci_water_pressure':'pressure','sci_water_temp':'temperature',
        # 'sci_water_cond':'conductivity','sci_water_sal':'salinity','sci_water_dens':'density','sci_flbbcd_bb_units':'turbidity',
        # 'sci_flbbcd_cdom_units':'cdom','sci_flbbcd_chlor_units':'chlorophyll'})
        ds = ds.rename({'index': 'time','sci_water_pressure':'pressure','sci_water_temp':'temperature',
        'sci_water_cond':'conductivity','sci_water_sal':'salinity','sci_water_dens':'density'})
    return ds

def process_flight_df(df:pd.DataFrame) -> pd.DataFrame:
    '''
    Process flight dataframe by filtering and calculating latitude and longitude and renaming variables
    '''
    # Exclude data before 2020 and after 2030
    df = df[(df['m_present_time'] > '2010-01-01') & (df['m_present_time'] < '2030-01-01')]
    # Convert pressure from db to dbar
    df['m_pressure'] = df['m_pressure'] * 10
    # Convert latitude and longitude to decimal degrees
    # .round(0) will up round the decimal numebr > 0.5 to 1, which is not working
    df['m_lat'] = df['m_lat'] / 100.0
    df['m_lat'] = np.sign(df['m_lat'])*(np.sign(df['m_lat'])*df['m_lat']-(np.sign(df['m_lat'])*df['m_lat'])%1 + (np.sign(df['m_lat'])*df['m_lat'])%1/0.6)

    df['m_lon'] = df['m_lon'] / 100.0
    df['m_lon'] = np.sign(df['m_lon'])*(np.sign(df['m_lon'])*df['m_lon']-(np.sign(df['m_lon'])*df['m_lon'])%1 + (np.sign(df['m_lon'])*df['m_lon'])%1/0.6)

    # Rename columns for clarity
    df.rename(columns={'m_lat': 'm_latitude', 'm_lon': 'm_longitude'}, inplace=True)

    return df

def convert_fli_df_to_ds(df:pd.DataFrame) -> xr.Dataset:
    ds = xr.Dataset.from_dataframe(df)
    return ds

def add_flight_attrs(ds:xr.Dataset) -> xr.Dataset:
    '''
    Add attributes to the flight dataset
    '''
    ds['m_pressure'].attrs = {'accuracy': 0.01,
    'ancillary_variables': ' ',
    'axis': 'Z',
    'bytes': 4,
    'comment': 'Alias for m_pressure, multiplied by 10 to convert from bar to dbar',
    'long_name': 'GPS Pressure',
    'observation_type': 'measured',
    'platform': 'platform',
    'positive': 'down',
    'precision': 0.01,
    'reference_datum': 'sea-surface',
    'resolution': 0.01,
    'source_sensor': 'sci_water_pressure',
    'standard_name': 'sea_water_pressure',
    'units': 'bar',
    'valid_max': 2000.0,
    'valid_min': 0.0,
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
    ds['m_water_depth'].attrs = {'accuracy': 0.01,
    'ancillary_variables': ' ',
    'axis': 'Z',
    'bytes': 4,
    'comment': 'Alias for m_depth',
    'long_name': 'GPS Depth',
    'observation_type': 'calculated',
    'platform': 'platform',
    'positive': 'down',
    'precision': 0.01,
    'reference_datum': 'sea-surface',
    'resolution': 0.01,
    'source_sensor': 'm_depth',
    'standard_name': 'sea_water_depth',
    'units': 'meters',
    'valid_max': 2000.0,
    'valid_min': 0.0,
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
    ds['m_latitude'].attrs = {'ancillary_variables': ' ',
    'axis': 'Y',
    'bytes': 8,
    'comment': 'm_gps_lat converted to decimal degrees and interpolated',
    'coordinate_reference_frame': 'urn:ogc:crs:EPSG::4326',
    'long_name': 'Latitude',
    'observation_type': 'calculated',
    'platform': 'platform',
    'precision': 5,
    'reference': 'WGS84',
    'source_sensor': 'm_gps_lat',
    'standard_name': 'latitude',
    'units': 'degree_north',
    'valid_max': 90.0,
    'valid_min': -90.0,
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
    ds['m_longitude'].attrs = {'ancillary_variables': ' ',
    'axis': 'X',
    'bytes': 8,
    'comment': 'm_gps_lon converted to decimal degrees and interpolated',
    'coordinate_reference_frame': 'urn:ogc:crs:EPSG::4326',
    'long_name': 'Longitude',
    'observation_type': 'calculated',
    'platform': 'platform',
    'precision': 5,
    'reference': 'WGS84',
    'source_sensor': 'm_gps_lon',
    'standard_name': 'longitude',
    'units': 'degree_east',
    'valid_max': 180.0,
    'valid_min': -180.0,
    'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}

    return ds

def format_flight_ds(ds:xr.Dataset) -> xr.Dataset:
    '''
    Format the flight dataset by sorting and renaming variables
    '''
    ds['index'] = np.sort(ds['m_present_time'].values.astype('datetime64[s]'))
    ds = ds.drop_vars('m_present_time')
    ds = ds.rename({'index': 'm_time','m_pressure':'m_pressure','m_water_depth':'depth','m_latitude':'latitude','m_longitude':'longitude'})

    return ds

def process_sci_data(science_data_dir,glider_id,glider,wmo_id) -> xr.Dataset:
    '''
    Perform all processing of science data from ascii to pandas dataframe to xarray dataset
    '''
    print_time('Processing Science Data')
    # Process Science Data
    sci_files = list(science_data_dir.rglob("*.asc"))
    sci_files.sort()
    df_sci = join_ascii_files(sci_files,read_sci_file)
    df_sci = process_sci_df(df_sci)
    ds_sci = convert_sci_df_to_ds(df_sci,glider_id,glider)
    ds_sci = add_sci_attrs(ds_sci,glider_id,glider,wmo_id)
    ds_sci = format_sci_ds(ds_sci)
    print_time('Finished Processing Science Data')
    return ds_sci

def process_flight_data(flight_data_dir) -> xr.Dataset:
    '''
    Perform all processing of flight data from ascii to pandas dataframe to xarray dataset
    '''
    print_time('Processing Flight Data')
    # Process Flight Data
    fli_files = list(flight_data_dir.rglob("*.asc"))
    fli_files.sort()
    df_fli = join_ascii_files(fli_files,read_flight_file)
    df_fli = process_flight_df(df_fli)
    ds_fli = convert_fli_df_to_ds(df_fli)
    ds_fli = add_flight_attrs(ds_fli)
    ds_fli = format_flight_ds(ds_fli)
    print_time('Finised Processing Flight Data')
    return ds_fli

@define
class Gridder:
    '''
    Object to create and calculate the gridded dataset
    This object handles some functions that are coupled and to make the code easier to read
    '''
    ds_mission:xr.Dataset
    interval_h:int|float = field(default=1)
    interval_p:int|float = field(default=0.1)

    ds:xr.Dataset = field(init=False)
    ds_gridded:xr.Dataset = field(init=False)
    variable_names:list = field(init=False)
    time:np.ndarray = field(init=False)
    pres:np.ndarray = field(init=False)
    lat:np.ndarray = field(init=False)
    lon:np.ndarray = field(init=False)
    xx:np.ndarray = field(init=False)
    yy:np.ndarray = field(init=False)
    int_time:np.ndarray = field(init=False)
    int_pres:np.ndarray = field(init=False)
    data_arrays:dict = field(init=False)
    grid_pres:np.ndarray = field(init=False)
    grid_time:np.ndarray = field(init=False)

    def __attrs_post_init__(self):
        # ds = xr.open_dataset(file)
        self.ds = self.ds_mission.copy()
        # Get indexes of where there are non-nan pressure values
        tloc_idx = np.where(~np.isnan(self.ds['pressure']))[0]
        # Select the times were thre are non-nan pressure values
        self.ds = self.ds.isel(time=tloc_idx)
        # Get all of the variables present in the dataset
        self.variable_names = list(self.ds.data_vars.keys())
        # Get all of the time values in the dataset
        self.time = self.ds.time.values
        # Get all of the pressure values in the dataset
        self.pres = self.ds.pressure.values
        # Get all of the lat and lon values in the dataset
        self.lon = np.nanmean(self.ds_mission.longitude)
        self.lat = np.nanmean(self.ds_mission.latitude[np.where(self.ds_mission.latitude.values<29.5)].values)

        self.initalize_grid()
    

    def initalize_grid(self):
        print_time('Initalizing Grid')
        start_hour = int(pd.to_datetime(self.time[0]).hour / self.interval_h) * self.interval_h
        end_hour = int(pd.to_datetime(self.time[-1]).hour / self.interval_h) * self.interval_h
        start_time = pd.to_datetime(self.time[0]).replace(hour=start_hour, minute=0, second=0)
        end_time = pd.to_datetime(self.time[-1]).replace(hour=end_hour, minute=0, second=0)

        self.int_time = np.arange(start_time, end_time+np.timedelta64(self.interval_h, 'h'), np.timedelta64(self.interval_h, 'h')).astype('datetime64[s]')

        # create the pressure grids for intepolation
        start_pres = 0
        end_pres = np.nanmax(self.pres)
        self.int_pres = np.arange(start_pres, end_pres, self.interval_p)

        self.grid_pres,self.grid_time = np.meshgrid(self.int_pres,self.int_time[1:]) # get the time between two time point
        self.xx,self.yy = np.shape(self.grid_pres)

        # List of variable names
        var_names = ['int_temp', 'int_salt', 'int_cond', 'int_dens', 'int_turb', 'int_cdom', 'int_chlo', 'int_oxy4']

        # Dictionary to store the arrays
        self.data_arrays = {}

        # Initialize each array with NaN values and store it in the dictionary
        for var in var_names:
            self.data_arrays[var] = np.empty((self.xx, self.yy))
            self.data_arrays[var].fill(np.nan)
        print_time('Finished Initalizing Grid')

    def add_attrs(self):
        self.ds_gridded['g_temp'].attrs = {'long_name': 'Gridded Temperature',
        'observation_type': 'calculated',
        'source': 'temperature from sci_water_temp',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_temperature',
        'units': 'Celsius',
        'valid_max': 40.0,
        'valid_min': -5.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_salt'].attrs = {'long_name': 'Gridded Salinity',
        'observation_type': 'calculated',
        'source': 'salinity from sci_water_sal',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_practical_salinity',
        'units': '1',
        'valid_max': 40.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_cond'].attrs = {'long_name': 'Gridded Conductivity',
        'observation_type': 'calculated',
        'source': 'conductivity from sci_water_cond',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_electrical_conductivity',
        'units': 'S m-1',
        'valid_max': 10.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_dens'].attrs = {'long_name': 'Gridded Density',
        'observation_type': 'calculated',
        'source': 'density from sci_water_dens',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_density',
        'units': 'kg m-3',
        'valid_max': 1040.0,
        'valid_min': 1015.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        if 'bb' in self.variable_names:
            self.ds_gridded['g_turb'].attrs = {'long_name': 'Gridded Turbidity',
            'observation_type': 'calculated',
            'source': 'turbidity from sci_flbbcd_bb_units',
            'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
            'standard_name': 'sea_water_turbidity',
            'units': '1',
            'valid_max': 1.0,
            'valid_min': 0.0,
            'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        if 'cdom' in self.variable_names:
            self.ds_gridded['g_cdom'].attrs = {'long_name': 'Gridded CDOM',
            'observation_type': 'calculated',
            'source': 'cdom from sci_flbbcd_cdom_units',
            'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
            'standard_name': 'concentration_of_colored_dissolved_organic_matter_in_sea_water',
            'units': 'ppb',
            'valid_max': 50.0,
            'valid_min': 0.0,
            'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        if 'chlor' in self.variable_names:
            self.ds_gridded['g_chlo'].attrs = {'long_name': 'Gridded Chlorophyll_a',
            'observation_type': 'calculated',
            'source': 'chlorophyll from sci_flbbcd_chlor_units',
            'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
            'standard_name': 'mass_concentration_of_chlorophyll_a_in_sea_water',
            'units': '\u03BCg/L',
            'valid_max': 10.0,
            'valid_min': 0.0,
            'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        if 'oxygen' in self.variable_names:
            self.ds_gridded['g_oxy4'].attrs = {'long_name': 'Gridded Oxygen',
            'observation_type': 'calculated',
            'source': 'oxygen from sci_oxy4_oxygen',
            'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
            'standard_name': 'moles_of_oxygen_per_unit_mass_in_sea_water',
            'units': '\u03BCmol/kg',
            'valid_max': 500.0,
            'valid_min': 0.0,
            'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_hc'].attrs = {'long_name': 'Gridded Heat Content',
        'observation_type': 'calculated',
        'source': 'g_temp, g_dens, cp=gsw.cp_t_exact, dz='+str(self.interval_p)+'dbar',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_heat_content_for_all_grids',
        'units': 'kJ/cm^2',
        'valid_max': 10.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_phc'].attrs = {'long_name': 'Gridded Potential Heat Content',
        'observation_type': 'calculated',
        'source': 'g_temp, g_dens, cp=gsw.cp_t_exact, dz='+str(self.interval_p)+'dbar',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_heat_content_for_grids_above_26°C',
        'units': 'kJ/cm^2',
        'valid_max': 10.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_sp'].attrs = {'long_name': 'Gridded Spiciness',
        'observation_type': 'calculated',
        'source': 'g_temp, g_salt, g_pres, lon, lat, via gsw.spiciness0',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'spiciness_from_absolute_salinity_and_conservative_temperature_at_0dbar',
        'units': 'kg/m^3',
        'valid_max': 10.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.ds_gridded['g_depth'].attrs = {'long_name': 'Gridded Depth',
        'observation_type': 'calculated',
        'source': 'g_pres, lat, via gsw.z_from_p',
        'resolution': str(self.interval_h)+'hour and '+str(self.interval_p)+'dbar',
        'standard_name': 'sea_water_depth',
        'units': 'm',
        'valid_max': 1000.0,
        'valid_min': 0.0,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}

    def create_gridded_dataset(self):
        print_time('Creating Gridded Data')
        for ttt in range(self.xx):
            tds:xr.Dataset = self.ds.sel(time=slice(str(self.int_time[ttt]),str(self.int_time[ttt+1]))).copy()
            if len(tds.time) > 0:
                tds = tds.sortby('pressure')
                tds = tds.assign_coords(time=('time',tds.time.values.astype('datetime64[s]')))
                tds['time'] = tds['pressure'].values
                
                # Remove duplicates and slightly modify if necessary by adding a tiny value
                unique_pressures, indices, counts = np.unique(tds['pressure'], return_index=True, return_counts=True)
                duplicates = unique_pressures[counts > 1]
                for pressure in duplicates:
                    rrr = np.where(tds['pressure'] == pressure)[0]
                    for rr in rrr:
                        modified_pressure = pressure + 0.000000000001*rr
                        tds['pressure'][rr] = modified_pressure
                tds['time'] = tds['pressure'].values # save new non-duplicates pressure
                self.data_arrays['int_temp'][ttt,:] = tds.temperature.interp(time=self.int_pres)
                self.data_arrays['int_salt'][ttt,:] = tds.salinity.interp(time=self.int_pres)
                self.data_arrays['int_cond'][ttt,:] = tds.conductivity.interp(time=self.int_pres)
                self.data_arrays['int_dens'][ttt,:] = tds.density.interp(time=self.int_pres)
                if 'oxygen' in self.variable_names:
                    self.data_arrays['int_oxy4'][ttt,:] = tds.oxygen.interp(time=self.int_pres)

        # give a dz instead of calculating the inter depth
        sa = gsw.SA_from_SP(self.data_arrays['int_salt'], self.grid_pres, self.lon, self.lat)
        pt = gsw.pt0_from_t(sa, self.data_arrays['int_temp'], self.grid_pres)
        ct = gsw.CT_from_pt(sa, pt)
        cp = gsw.cp_t_exact(sa, self.data_arrays['int_temp'], self.grid_pres) * 0.001 # from J/(kg*K) to kJ/(kg*°C) or use 3.85 as a constant?
        dep = gsw.z_from_p(self.grid_pres, self.lat, geo_strf_dyn_height=0, sea_surface_geopotential=0)
        spc = gsw.spiciness0(sa, ct)

        dz = self.interval_p
        hc = dz*cp*self.data_arrays['int_temp']*self.data_arrays['int_dens'] # deltaZ * Cp * temperature * density in the unit as $[kJ/m^2]$ * 10**-4 to $[kJ/cm^2]$
        phc = dz*cp*(self.data_arrays['int_temp']-26)*self.data_arrays['int_dens'] # deltaZ * Cp * temperature * density in the unit as $[kJ/m^2]$ * 10**-4 to $[kJ/cm^2]$
        phc[phc<0] = np.nan
        self.ds_gridded = xr.Dataset()
        self.ds_gridded['g_temp'] = xr.DataArray(self.data_arrays['int_temp'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_salt'] = xr.DataArray(self.data_arrays['int_salt'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_cond'] = xr.DataArray(self.data_arrays['int_cond'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_dens'] = xr.DataArray(self.data_arrays['int_dens'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        if 'oxygen' in self.variable_names:
            self.ds_gridded['g_oxy4'] = xr.DataArray(self.data_arrays['int_oxy4'],[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_hc'] = xr.DataArray(hc*10**-4,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_phc'] = xr.DataArray(phc*10**-4,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_sp'] = xr.DataArray(spc,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])
        self.ds_gridded['g_depth'] = xr.DataArray(dep,[('g_time',self.int_time[1:]),('g_pres',self.int_pres)])

        self.add_attrs()
        print_time('Finished Creating Gridded Data')

def add_gridded_data(ds_mission:xr.Dataset) -> xr.Dataset:
    '''
    Create gridder object and create the gridded dataset
    '''
    print_time('Adding Gridded Data')
    gridder = Gridder(ds_mission=ds_mission)
    gridder.create_gridded_dataset()
    ds_mission.update(gridder.ds_gridded)
    print_time('Finished Adding Gridded Data')
    return ds_mission

def get_polygon_coords(ds_mission:xr.Dataset) -> str:
    # get the POLYGON coordinates
    lat_max = np.nanmax(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)
    lat_min = np.nanmin(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)
    lon_max = np.nanmax(ds_mission.longitude.values)
    lon_min = np.nanmin(ds_mission.longitude.values)
    polygon_1 = str(lat_max)+' '+str(ds_mission.longitude[np.where(ds_mission.latitude==lat_max)[0][0]].values) # northmost
    polygon_2 = str(ds_mission.latitude[np.where(ds_mission.longitude==lon_max)[0][0]].values)+' '+str(lon_max) # eastmost
    polygon_3 = str(lat_min)+' '+str(ds_mission.longitude[np.where(ds_mission.latitude==lat_min)[0][0]].values) # southmost
    polygon_4 = str(ds_mission.latitude[np.where(ds_mission.longitude==lon_min)[0][0]].values)+' '+str(lon_min) # westmost
    polygon_5 = polygon_1
    return 'POLYGON (('+polygon_1+' '+polygon_2+' '+polygon_3+' '+polygon_4+' '+polygon_5+'))'

def add_global_attrs(ds_mission:xr.Dataset,mission_title:str,wmo_id:dict,glider:str) -> xr.Dataset:
    ''''''
    ds_mission.attrs = {'Conventions': 'CF-1.6, COARDS, ACDD-1.3',
    'acknowledgment': ' ',
    'cdm_data_type': 'Profile',
    'comment': 'time is the ctd_time from sci_m_present_time, m_time is the gps_time from m_present_time, g_time and g_pres are the grided time and pressure',
    'contributor_name': 'Steven F. DiMarco',
    'contributor_role': ' ',
    'creator_email': 'sakib@tamu.edu, gexiao@tamu.edu',
    'creator_institution': 'Texas A&M University, Geochemical and Environmental Research Group',
    'creator_name': 'Sakib Mahmud, Xiao Ge',
    'creator_type': 'persons',
    'creator_url': 'https://gerg.tamu.edu/',
    'date_created': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
    'date_issued': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
    'date_metadata_modified': '2023-09-15',
    'date_modified': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
    'deployment': ' ',
    'featureType': 'profile',
    'geospatial_bounds_crs': 'EPSG:4326',
    'geospatial_bounds_vertical_crs': 'EPSG:5831',
    'geospatial_lat_resolution': "{:.4e}".format(abs(np.nanmean(np.diff(ds_mission.latitude))))+ ' degree',
    'geospatial_lat_units': 'degree_north',
    'geospatial_lon_resolution': "{:.4e}".format(abs(np.nanmean(np.diff(ds_mission.longitude))))+ ' degree',
    'geospatial_lon_units': 'degree_east',
    'geospatial_vertical_positive': 'down',
    'geospatial_vertical_resolution': ' ',
    'geospatial_vertical_units': 'EPSG:5831',
    'infoUrl': 'https://gerg.tamu.edu/',
    'institution': 'Texas A&M University, Geochemical and Environmental Research Group',
    'instrument': 'In Situ/Laboratory Instruments > Profilers/Sounders > CTD',
    'instrument_vocabulary': 'NASA/GCMD Instrument Keywords Version 8.5',
    'ioos_regional_association': 'GCOOS-RA',
    'keywords': 'Oceans > Ocean Pressure > Water Pressure, Oceans > Ocean Temperature > Water Temperature, Oceans > Salinity/Density > Conductivity, Oceans > Salinity/Density > Density, Oceans > Salinity/Density > Salinity',
    'keywords_vocabulary': 'NASA/GCMD Earth Sciences Keywords Version 8.5',
    'license': 'This data may be redistributed and used without restriction.  Data provided as is with no expressed or implied assurance of quality assurance or quality control',
    'metadata_link': ' ',
    'naming_authority': 'org.gcoos.gandalf',
    'ncei_template_version': 'NCEI_NetCDF_Trajectory_Template_v2.0',
    'platform': 'In Situ Ocean-based Platforms > AUVS > Autonomous Underwater Vehicles',
    'platform_type': 'Slocum Glider',
    'platform_vocabulary': 'NASA/GCMD Platforms Keywords Version 8.5',
    'processing_level': 'Level 0',
    'product_version': '0.0',
    'program': ' ',
    'project': ' ',
    'publisher_email': 'sdimarco@tamu.edu',
    'publisher_institution': 'Texas A&M University, Geochemical and Environmental Research Group',
    'publisher_name': 'Steven F. DiMarco',
    'publisher_url': 'https://gerg.tamu.edu/',
    'references': ' ',
    'sea_name': 'Gulf of Mexico',
    'standard_name_vocabulary': 'CF Standard Name Table v27',
    'summary': 'Merged dataset for GERG future usage.',
    'time_coverage_resolution': ' ',
    'wmo_id': wmo_id[glider],
    'uuid': str(uuid.uuid4()),
    'history': 'dbd and ebd files transferred from dbd2asc on 2023-09-15, merged into single netCDF file on '+pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
    'title': mission_title,
    'source': 'Observational Slocum glider data from source ebd and dbd files',
    'geospatial_lat_min': str(np.nanmin(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)),
    'geospatial_lat_max': str(np.nanmax(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)),
    'geospatial_lon_min': str(np.nanmin(ds_mission.longitude.values)),
    'geospatial_lon_max': str(np.nanmax(ds_mission.longitude.values)),
    'geospatial_bounds': get_polygon_coords(ds_mission),
    'geospatial_vertical_min': str(np.nanmin(ds_mission.depth[np.where(ds_mission.depth>0)].values)),
    'geospatial_vertical_max': str(np.nanmax(ds_mission.depth.values)),
    'time_coverage_start': str(ds_mission.time[-1].values)[:19],
    'time_coverage_end': str(ds_mission.m_time[-1].values)[:19],
    'time_coverage_duration': 'PT'+str((ds_mission.m_time[-1].values - ds_mission.time[-1].values) / np.timedelta64(1, 's'))+'S'}

    return ds_mission

def save_ds(ds_mission:xr.Dataset,output_nc_path):
    '''
    Save xarray.Dataset to NetCDF
    '''
    print_time('Saving Dataset to NetCDF')
    ds_mission.to_netcdf(output_nc_path)
    print_time('Done Saving Dataset to NetCDF')

def convert_ascii_to_dataset(working_directory:Path,glider:str,mission_title:str):
    '''
    Convert ascii data files into a single NetCDF file
    '''
    print_time('Converting ascii to netcdf')
    working_directory = working_directory.joinpath('processed')

    science_data_dir:Path = working_directory.joinpath('Science')
    flight_data_dir:Path = working_directory.joinpath('Flight')

    # output_nc_path = working_directory.joinpath('processed','nc',nc_filename)

    glider_id = {'199':'Dora','307':'Reveille','308':'Howdy','540':'Stommel','541':'Sverdrup'}
    wmo_id = {'199':'unknown','307':'4801938','308':'4801915','540':'4801916','541':'4801924'}
    

    # Process Science Data
    ds_sci:xr.Dataset = process_sci_data(science_data_dir,glider_id,glider,wmo_id)

    # Make a copy of the science dataset
    ds_mission:xr.Dataset = ds_sci.copy()

    # Process Flight Data
    ds_fli:xr.Dataset = process_flight_data(flight_data_dir)

    # Add flight data to mission dataset
    ds_mission.update(ds_fli)

    # Add gridded data to mission dataset
    ds_mission = add_gridded_data(ds_mission)

    # Add attributes to the mission dataset
    ds_mission = add_global_attrs(ds_mission,mission_title=mission_title,wmo_id=wmo_id,glider=glider)

    # Export the mission dataset as a NetCDF
    # return ds_mission
    # save_ds(ds_mission,output_nc_path)
    # ds_mission.close()
    print_time('Finished converting ascii to dataset')
    return ds_mission

# def test(ds_mission):
#     '''
#     Create figures from the dataset to test the production
#     '''
#     import cmocean.cm as cmo
#     import seaborn as sns
#     import matplotlib.pyplot as plt
#     sns.set_style("darkgrid")
#     plt.figure()
#     plt.scatter(ds_mission.salinity,ds_mission.temperature,c='C0')
#     plt.scatter(ds_mission.g_salt,ds_mission.g_temp,c='C1',alpha=0.3)
#     plt.figure()
#     plt.scatter(ds_mission.time.values,ds_mission['pressure'].values,c=ds_mission.density,s=1,cmap=cmo.dense);plt.colorbar();plt.gca().invert_yaxis()
#     plt.figure()
#     plt.pcolormesh(ds_mission.g_time.values,ds_mission.g_pres,ds_mission.g_dens.T,cmap=cmo.dense);plt.colorbar();plt.gca().invert_yaxis()
#     plt.figure()
#     plt.pcolormesh(ds_mission.g_time.values,ds_mission.g_pres,ds_mission.g_hc.T,cmap=cmo.thermal);plt.colorbar();plt.contour(ds_mission.g_time.values,ds_mission.g_pres,ds_mission.g_sp.T,cmap=cmo.dense);plt.gca().invert_yaxis()
#     plt.figure()
#     sns.set_style("darkgrid")
#     sns.histplot(np.diff(ds_mission['pressure'].values), kde=True, color='C0');plt.xlim(-0.2,0.5)

#     for var in ds_mission.data_vars:
#         print(var,ds_mission[var].attrs)


