import numpy as np
import pandas as pd
import xarray as xr
import dbdreader
from pathlib import Path
import datetime
import gsw

from glider_ingest.utils import print_time


def get_sci_vars(variables:list):
    # Define subsets of columns based on the presence of sci_oxy4_oxygen and sci_flbbcd_bb_units
    if 'sci_oxy4_oxygen' in variables and 'sci_flbbcd_bb_units' in variables:
            present_variables = ['sci_flbbcd_bb_units', 'sci_flbbcd_cdom_units', 'sci_flbbcd_chlor_units', 'sci_water_pressure', 'sci_water_temp', 'sci_water_cond', 'sci_oxy4_oxygen']

    elif 'sci_oxy4_oxygen' in variables and 'sci_flbbcd_bb_units' not in variables:
            present_variables = ['sci_water_pressure', 'sci_water_temp', 'sci_water_cond', 'sci_oxy4_oxygen']

    elif 'sci_oxy4_oxygen' not in variables and 'sci_flbbcd_bb_units' in variables:
            present_variables = ['sci_flbbcd_bb_units', 'sci_flbbcd_cdom_units', 'sci_flbbcd_chlor_units', 'sci_water_pressure', 'sci_water_temp', 'sci_water_cond']

    elif 'sci_oxy4_oxygen' not in variables and 'sci_flbbcd_bb_units' not in variables:
            present_variables = ['sci_water_pressure', 'sci_water_temp', 'sci_water_cond']

    return present_variables

def load_science(files,cache_loc,mission_start_date:str='2010-01-01'):

    dbd = dbdreader.MultiDBD(files,cacheDir=cache_loc)
    # return dbd
    variables = dbd.parameterNames['sci']
    present_variables = get_sci_vars(variables)
    vars = dbd.get_sync(*present_variables)

    df = pd.DataFrame(vars).T

    column_names = ['sci_m_present_time']
    column_names.extend(present_variables)

    df.columns = column_names

    df['sci_m_present_time'] = pd.to_datetime(df['sci_m_present_time'], unit='s', errors='coerce')
    df = df.dropna()

    # Remove any data with erroneous dates (outside expected dates 2010 through currentyear+1)
    upper_date_limit = str(datetime.datetime.today().date()+datetime.timedelta(days=365))
    # start_date = '2010-01-01'
    # df = df.reset_index()
    df = df.loc[(df['sci_m_present_time'] > mission_start_date) & (df['sci_m_present_time'] < upper_date_limit)]

    # Convert pressure from db to dbar
    df['sci_water_pressure'] = df['sci_water_pressure'] * 10
    # Calculate salinity and density
    df['sci_water_sal'] = gsw.SP_from_C(df['sci_water_cond']*10,df['sci_water_temp'],df['sci_water_pressure'])
    CT = gsw.CT_from_t(df['sci_water_sal'],df['sci_water_temp'],df['sci_water_pressure'])
    df['sci_water_dens'] = gsw.rho_t_exact(df['sci_water_sal'],CT,df['sci_water_pressure'])

    df = df.dropna()
    dbd.close()
    return df

def convert_sci_df_to_ds(df:pd.DataFrame,glider_id:str) -> xr.Dataset:
    '''Convert the given science dataframe to a xarray dataset'''
    bds = xr.Dataset() # put the platform info into the dataset on the top
    bds['platform'] = xr.DataArray(glider_id)
    ds = xr.Dataset.from_dataframe(df)
    ds = bds.update(ds)
    return ds


def add_sci_attrs(ds:xr.Dataset,glider_id:str,wmo_id:str) -> xr.Dataset:
    '''Add attributes to the science dataset'''
    variables = list(ds.data_vars)
    # Define variable attributes
    ds['platform'].attrs = {'ancillary_variables': ' ',
    'comment': ' ',
    'id': glider_id,
    'instruments': 'instrument_ctd',
    'long_name': 'Slocum Glider '+ glider_id,
    'type': 'platform',
    'wmo_id': wmo_id,
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

def process_sci_data(files,cache_loc,glider_id,wmo_id,mission_start_date) -> xr.Dataset:
    '''Perform all processing of science data from ascii to pandas dataframe to xarray dataset'''
    print_time('Processing Science Data')
    # Process Science Data
    df_sci = load_science(files,cache_loc,mission_start_date)
    ds_sci = convert_sci_df_to_ds(df_sci,glider_id)
    ds_sci = add_sci_attrs(ds_sci,glider_id,wmo_id)
    ds_sci = format_sci_ds(ds_sci)
    print_time('Finished Processing Science Data')
    return ds_sci

# sds_sci = process_sci_data(glider_id='1148',wmo_id='4801915',mission_start_date='2024-01-01')
