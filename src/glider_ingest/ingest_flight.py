import numpy as np
import pandas as pd
import xarray as xr
import dbdreader
from pathlib import Path
import datetime

from glider_ingest.utils import print_time

def load_flight(files,cache_loc,mission_start_date):
    # files = list(Path("G:/Shared drives/Slocum Gliders/Mission Data & Files/2024 Missions/Mission 46/Memory card copy/Flight_card/logs").rglob("*.dbd"))
    # files = [str(file) for file in files][:20]
    # cache_loc = "G:/Shared drives/Slocum Gliders/Mission Data & Files/2024 Missions/Mission 46/Memory card copy/Flight_card/state/cache"
    dbd = dbdreader.MultiDBD(files,cacheDir=cache_loc)

    test = dbd.get_sync('m_lat', 'm_lon', 'm_pressure','m_water_depth')

    df = pd.DataFrame(test).T

    df.columns = ['m_present_time', 'm_lat', 'm_lon', 'm_pressure','m_water_depth']

    df['m_present_time'] = pd.to_datetime(df['m_present_time'],unit='s')

    '''Process flight dataframe by filtering and calculating latitude and longitude and renaming variables.'''
    # Remove any data with erroneous dates (outside expected dates 2010 through currentyear+1)
    upper_date_limit = str(datetime.datetime.today().date()+datetime.timedelta(days=365))
    # start_date = '2010-01-01'
    df = df.loc[(df['m_present_time'] > mission_start_date) & (df['m_present_time'] < upper_date_limit)]
    # Convert pressure from db to dbar
    df['m_pressure'] *= 10
    
    # Convert latitude and longitude to decimal degrees in one step using vectorization
    df['m_lat'] /= 100.0
    lat_sign = np.sign(df['m_lat'])
    df['m_lat'] = lat_sign * (np.floor(np.abs(df['m_lat'])) + (np.abs(df['m_lat']) % 1) / 0.6)

    df['m_lon'] /= 100.0
    lon_sign = np.sign(df['m_lon'])
    df['m_lon'] = lon_sign * (np.floor(np.abs(df['m_lon'])) + (np.abs(df['m_lon']) % 1) / 0.6)

    # Rename columns for clarity
    df.rename(columns={'m_lat': 'm_latitude', 'm_lon': 'm_longitude'}, inplace=True)
    df = df.dropna()

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


def process_flight_data(files,cache_loc,mission_start_date) -> xr.Dataset:
    '''Perform all processing of flight data from dbd to pandas dataframe to xarray dataset'''
    # Process Flight Data
    print_time('Processing Flight Data')
    df_fli = load_flight(files,cache_loc,mission_start_date)
    ds_fli = convert_fli_df_to_ds(df_fli)
    ds_fli = add_flight_attrs(ds_fli)
    ds_fli = format_flight_ds(ds_fli)
    print_time('Finised Processing Flight Data')
    return ds_fli

