'''
Module containing utilities for the package
'''
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from gridder import Gridder

# AUTHORS:
# Sakib Mahmud, Texas A&M University, Geochemical and Environmental Research Group, sakib@tamu.edu
# Xiao Ge, Texas A&M University, Geochemical and Environmental Research Group, gexiao@tamu.edu
# Alec Krueger, Texas A&M University, Geochemical and Environmental Research Group, alecmkrueger@tamu.edu


# Define functions and classes
def print_time(message):
    '''Add the current time to the end of a message'''
    # Get current time
    current_time = datetime.datetime.today().strftime('%H:%M:%S')
    # Add time to message
    whole_message = f'{message}: {current_time}'
    # Print out the message
    print(whole_message)

def length_validator(instance, attribute, value):
    '''Validator to ensure the attribute has exactly length 2.'''
    if len(value) != 2:
        raise ValueError(f"The '{attribute.name}' attribute must have a length of exactly 2.")

def copy_file(input_file_path, output_file_path):
    '''Use shutil to copy and the input file to the output location'''
    shutil.copy2(input_file_path, output_file_path)

def clean_dir(dir:Path):
    files = dir.rglob('*')
    [os.remove(file) for file in files]
    print(f'Removed all files in {dir}')
    

def rename_file(rename_files_path, file):
    '''Use subprocess to run the executable file with the rename_files_path input'''
    subprocess.run([rename_files_path, file])

def convert_file(binary2asc_path:Path, raw_file, ascii_file):
    '''Use os.system to run the binary2asc executable on the raw file and output the ascii_file'''
    cmd = f'{binary2asc_path} "{raw_file}" > "{ascii_file}"'
    os.system(cmd)

def create_tasks(working_directory,data_source,extension,output_data_dir,tasks,binary2asc_path):
    '''Create tasks for the ThreadPoolExecutor in the convert_binary_to_ascii function'''
    raw_files = working_directory.joinpath(data_source).joinpath(extension).rglob('*')
    for raw_file in raw_files:
        ascii_file = output_data_dir.joinpath(data_source, f'{raw_file.name}.asc')
        tasks.append((binary2asc_path, raw_file, ascii_file))
    return tasks

def read_sci_file(file:Path) -> pd.DataFrame:
    '''Tries to read a file from science and filters to select a few variables'''
    # Check if there are enough lines to read the file if there are not then return None,
    # any Nones are handled by the pd.concat function in join_ascii_files
    try:
        if os.path.getsize(file) > 0:
            # Read in the data
            df_raw = pd.read_csv(file, header=14, sep=' ', skiprows=[15,16])

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
            df_filtered = df_filtered.assign(sci_m_present_time=dates_datetime)
            df_filtered = df_filtered.set_index('sci_m_present_time')
        else:
            # Set the dataframe to 
            df_filtered = None
    except Exception as e:
        print(f'Unable to read and skipping: {file.stem} due to {e}')
        df_filtered = None
    
    return df_filtered

def read_flight_file(file:Path) -> pd.DataFrame:
    '''Tries to read flight data and filteres to select a few variables'''
    try:
        # Check if there are enough lines of data to read
        if os.path.getsize(file) > 0:
            df_raw = pd.read_csv(file, header=14, sep=' ', skiprows=[15,16])
            present_variables = ['m_present_time','m_lat','m_lon','m_pressure','m_water_depth']
            df_filtered = df_raw[present_variables]
            # Parse the timestamp explicitly
            dates = df_filtered['m_present_time'].copy()
            dates_datetime =  pd.to_datetime(dates, unit='s', errors='coerce')
            df_filtered = df_filtered.assign(m_present_time=dates_datetime)
            df_filtered = df_filtered.set_index(['m_present_time'])
        else:
            df_filtered = None
    except Exception as e:
        print(f'Unable to read and skipping: {file.stem} due to {e}')
        df_filtered = None
    
    return df_filtered

def join_ascii_files(files, file_reader, max_workers=None) -> pd.DataFrame:
    '''Uses ThreadPoolExecutor to read all files using a file reader function then concatenates all the files.'''
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
    df_list = [df for df in df_list if df is not None]
    df_list = [df for df in df_list if not df.empty]
    df_list = [df for df in df_list if len(df) > 0]
    df_concat = pd.concat(df_list, axis=0)
    return df_concat

def process_sci_df(df:pd.DataFrame) -> pd.DataFrame:
    '''Process the data to filter and calculate salinity and density'''
    # Remove any data with erroneous dates (outside expected dates 2010-2030)
    upper_date_limit = str(datetime.datetime.today().date()+datetime.timedelta(days=365))
    df = df.reset_index()
    df = df[(df['sci_m_present_time'] > '2010-01-01') & (df['sci_m_present_time'] < upper_date_limit)]
    # Convert pressure from db to dbar
    df['sci_water_pressure'] = df['sci_water_pressure'] * 10
    # Calculate salinity and density
    df['sci_water_sal'] = gsw.SP_from_C(df['sci_water_cond']*10,df['sci_water_temp'],df['sci_water_pressure'])
    CT = gsw.CT_from_t(df['sci_water_sal'],df['sci_water_temp'],df['sci_water_pressure'])
    df['sci_water_dens'] = gsw.rho_t_exact(df['sci_water_sal'],CT,df['sci_water_pressure'])
    return df

def convert_sci_df_to_ds(df:pd.DataFrame,glider_id:dict,glider:str) -> xr.Dataset:
    '''Convert the given science dataframe to a xarray dataset'''
    bds = xr.Dataset() # put the platform info into the dataset on the top
    bds['platform'] = xr.DataArray(glider_id[glider])
    ds = xr.Dataset.from_dataframe(df)
    ds = bds.update(ds)
    return ds

def add_sci_attrs(ds:xr.Dataset,glider_id,glider,wmo_id) -> xr.Dataset:
    '''Add attributes to the science dataset'''
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
    '''Format the science dataset by sorting and renameing variables'''
    ds['index'] = np.sort(ds['sci_m_present_time'].values.astype('datetime64[ns]'))
    ds = ds.drop_vars('sci_m_present_time')
    if 'sci_oxy4_oxygen' in ds.data_vars.keys():
        ds = ds.rename({'index': 'time','sci_water_pressure':'pressure','sci_water_temp':'temperature',
        'sci_water_cond':'conductivity','sci_water_sal':'salinity','sci_water_dens':'density','sci_flbbcd_bb_units':'turbidity',
        'sci_flbbcd_cdom_units':'cdom','sci_flbbcd_chlor_units':'chlorophyll','sci_oxy4_oxygen':'oxygen'})
    else:

        ds = ds.rename({'index': 'time','sci_water_pressure':'pressure','sci_water_temp':'temperature',
        'sci_water_cond':'conductivity','sci_water_sal':'salinity','sci_water_dens':'density'})
    return ds

def process_flight_df(df:pd.DataFrame) -> pd.DataFrame:
    '''Process flight dataframe by filtering and calculating latitude and longitude and renaming variables'''
    # Exclude data before 2020 and after 2030
    df = df.reset_index()
    df = df[(df['m_present_time'] > '2010-01-01') & (df['m_present_time'] < '2030-01-01')]
    # Convert pressure from db to dbar
    df['m_pressure'] = df['m_pressure'] * 10
    # Convert latitude and longitude to decimal degrees
    # .round(0) will up round the decimal number > 0.5 to 1, which is not working
    df['m_lat'] = df['m_lat'] / 100.0
    df['m_lat'] = np.sign(df['m_lat'])*(np.sign(df['m_lat'])*df['m_lat']-(np.sign(df['m_lat'])*df['m_lat'])%1 + (np.sign(df['m_lat'])*df['m_lat'])%1/0.6)

    df['m_lon'] = df['m_lon'] / 100.0
    df['m_lon'] = np.sign(df['m_lon'])*(np.sign(df['m_lon'])*df['m_lon']-(np.sign(df['m_lon'])*df['m_lon'])%1 + (np.sign(df['m_lon'])*df['m_lon'])%1/0.6)

    # Rename columns for clarity
    df.rename(columns={'m_lat': 'm_latitude', 'm_lon': 'm_longitude'}, inplace=True)

    return df

def convert_fli_df_to_ds(df:pd.DataFrame) -> xr.Dataset:
    '''Convert the flight dataframe to dataset'''
    ds = xr.Dataset.from_dataframe(df)
    return ds

def add_flight_attrs(ds:xr.Dataset) -> xr.Dataset:
    '''Add attributes to the flight dataset'''
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
    '''Format the flight dataset by sorting and renaming variables'''
    ds['index'] = np.sort(ds['m_present_time'].values.astype('datetime64[ns]'))
    ds = ds.drop_vars('m_present_time')
    ds = ds.rename({'index': 'm_time','m_pressure':'m_pressure','m_water_depth':'depth','m_latitude':'latitude','m_longitude':'longitude'})

    return ds

def process_sci_data(science_data_dir,glider_id,glider,wmo_id) -> xr.Dataset:
    '''Perform all processing of science data from ascii to pandas dataframe to xarray dataset'''
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
    '''Perform all processing of flight data from ascii to pandas dataframe to xarray dataset'''
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

def add_gridded_data(ds_mission:xr.Dataset) -> xr.Dataset:
    '''Create gridder object and create the gridded dataset'''
    print_time('Adding Gridded Data')
    gridder = Gridder(ds_mission=ds_mission)
    gridder.create_gridded_dataset()
    ds_mission.update(gridder.ds_gridded)
    print_time('Finished Adding Gridded Data')
    return ds_mission

def get_polygon_coords(ds_mission:xr.Dataset) -> str:
    '''Get the polygon coords for the dataset global attributes'''
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
    '''Add attributes to the mission dataset'''
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
    '''Save xarray.Dataset to NetCDF'''
    print_time('Saving Dataset to NetCDF')
    ds_mission.to_netcdf(output_nc_path)
    print_time('Done Saving Dataset to NetCDF')

def convert_ascii_to_dataset(working_directory:Path,glider:str,mission_title:str):
    '''Convert ascii data files into a single NetCDF file'''
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

    print_time('Finished converting ascii to dataset')
    return ds_mission

