import numpy as np
import pandas as pd
import xarray as xr
import dbdreader
import gsw
from attrs import define

from glider_ingest.MissionData import MissionData
from glider_ingest.utils import print_time


@define
class ScienceProcessor:

    mission_data:MissionData

    def get_sci_vars(self,variables:list):
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

    def load_science(self):
        files = self.mission_data.get_files(files_loc=self.mission_data.sci_files_loc,extension='ebd')
        dbd = dbdreader.MultiDBD(files,cacheDir=self.mission_data.sci_cache_loc)

        all_variables = dbd.parameterNames['sci']
        present_variables = self.get_sci_vars(all_variables)
        vars = dbd.get_sync(*present_variables)

        self.mission_data.df_sci = pd.DataFrame(vars).T

        column_names = ['sci_m_present_time']
        column_names.extend(present_variables)

        self.mission_data.df_sci.columns = column_names

        self.mission_data.df_sci['sci_m_present_time'] = pd.to_datetime(self.mission_data.df_sci['sci_m_present_time'], unit='s', errors='coerce')
        self.mission_data.df_sci = self.mission_data.df_sci.dropna()

        # Remove data with erroneous dates
        vaild_dates_mask = (self.mission_data.df_sci['sci_m_present_time'] >= self.mission_data.mission_start_date) & (self.mission_data.df_sci['sci_m_present_time'] <= self.mission_data.mission_end_date)
        self.mission_data.df_sci = self.mission_data.df_sci.loc[vaild_dates_mask]

        # Convert pressure from db to dbar
        self.mission_data.df_sci['sci_water_pressure'] = self.mission_data.df_sci['sci_water_pressure'] * 10
        # Calculate salinity and density
        self.mission_data.df_sci['sci_water_sal'] = gsw.SP_from_C(self.mission_data.df_sci['sci_water_cond']*10,self.mission_data.df_sci['sci_water_temp'],self.mission_data.df_sci['sci_water_pressure'])
        CT = gsw.CT_from_t(self.mission_data.df_sci['sci_water_sal'],self.mission_data.df_sci['sci_water_temp'],self.mission_data.df_sci['sci_water_pressure'])
        self.mission_data.df_sci['sci_water_dens'] = gsw.rho_t_exact(self.mission_data.df_sci['sci_water_sal'],CT,self.mission_data.df_sci['sci_water_pressure'])

        self.mission_data.df_sci = self.mission_data.df_sci.dropna()
        dbd.close()
        return self.mission_data.df_sci

    def convert_sci_df_to_ds(self) -> xr.Dataset:
        '''Convert the given science dataframe to a xarray dataset'''
        platform_ds = xr.Dataset() # put the platform info into the dataset on the top
        platform_ds['platform'] = xr.DataArray(self.mission_data.glider_id)
        self.mission_data.ds_sci = xr.Dataset.from_dataframe(self.mission_data.df_sci)
        self.mission_data.ds_sci = platform_ds.update(self.mission_data.ds_sci)


    def add_sci_attrs(self) -> xr.Dataset:
        '''Add attributes to the science dataset'''
        variables = list(self.mission_data.ds_sci.data_vars)
        # Define variable attributes
        self.mission_data.ds_sci['platform'].attrs = {'ancillary_variables': ' ',
        'comment': ' ',
        'id': self.mission_data.glider_id,
        'instruments': 'instrument_ctd',
        'long_name': 'Slocum Glider '+ self.mission_data.glider_id,
        'type': 'platform',
        'wmo_id': self.mission_data.wmo_id,
        'update_time': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')}
        self.mission_data.ds_sci['sci_water_pressure'].attrs = {'accuracy': 0.01,
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
        self.mission_data.ds_sci['sci_water_temp'].attrs = {'accuracy': 0.004,
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
        self.mission_data.ds_sci['sci_water_cond'].attrs = {'accuracy': 0.001,
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
        self.mission_data.ds_sci['sci_water_sal'].attrs = {'accuracy': ' ',
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
        self.mission_data.ds_sci['sci_water_dens'].attrs = {'accuracy': ' ',
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
            self.mission_data.ds_sci['sci_flbbcd_bb_units'].attrs = {'long_name':'science turbidity', 'standard_name':'backscatter', 'units':'nodim'}
            self.mission_data.ds_sci['sci_flbbcd_bb_units'].attrs = {'accuracy': ' ',
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
            self.mission_data.ds_sci['sci_flbbcd_cdom_units'].attrs = {'accuracy': ' ',
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
            self.mission_data.ds_sci['sci_flbbcd_chlor_units'].attrs = {'accuracy': ' ',
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
            self.mission_data.ds_sci['sci_oxy4_oxygen'].attrs = {'accuracy': ' ',
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

    def format_sci_ds(self) -> xr.Dataset:
        '''Format the science dataset by sorting and renameing variables'''
        self.mission_data.ds_sci['index'] = np.sort(self.mission_data.ds_sci['sci_m_present_time'].values.astype('datetime64[ns]'))
        self.mission_data.ds_sci = self.mission_data.ds_sci.drop_vars('sci_m_present_time')
        if 'sci_oxy4_oxygen' in self.mission_data.ds_sci.data_vars.keys():
            self.mission_data.ds_sci = self.mission_data.ds_sci.rename({'index': 'time','sci_water_pressure':'pressure','sci_water_temp':'temperature',
            'sci_water_cond':'conductivity','sci_water_sal':'salinity','sci_water_dens':'density','sci_flbbcd_bb_units':'turbidity',
            'sci_flbbcd_cdom_units':'cdom','sci_flbbcd_chlor_units':'chlorophyll','sci_oxy4_oxygen':'oxygen'})
        else:
            self.mission_data.ds_sci = self.mission_data.ds_sci.rename({'index': 'time','sci_water_pressure':'pressure','sci_water_temp':'temperature',
            'sci_water_cond':'conductivity','sci_water_sal':'salinity','sci_water_dens':'density'})

    def process_sci_data(self) -> xr.Dataset:
        '''Perform all processing of science data from ascii to pandas dataframe to xarray dataset'''
        print_time('Processing Science Data')
        # Process Science Data
        self.load_science()
        self.convert_sci_df_to_ds()
        self.add_sci_attrs()
        self.format_sci_ds()
        # self.mission_data.get_output_nc_path()
        print_time('Finished Processing Science Data')

