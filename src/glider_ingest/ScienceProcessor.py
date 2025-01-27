import numpy as np
import pandas as pd
import xarray as xr
import dbdreader
import gsw
from attrs import define

from glider_ingest.MissionData import MissionData
from glider_ingest.variable import Variable
from glider_ingest.utils import print_time

@define
class ScienceProcessor:
    """
    A class to process science data from glider missions.

    This class handles the loading, processing, and conversion of science data
    from raw files into a structured dataset, while also performing variable
    calculations and renaming for consistency.

    Attributes
    ----------
    mission_data : MissionData
        An instance of the MissionData class containing mission-related configurations and data storage.
    """

    mission_data: MissionData

    def filter_sci_vars(self, variables: list):
        """
        Determine the subset of science variables to process based on their presence.

        Parameters
        ----------
        variables : list
            A list of available science variables from the mission data.

        Returns
        -------
        list
            A list of science variables that are present and should be processed.
        """        
        # If 'sci_oxy4_oxygen' is not present, remove its data_source_name from the list
        if 'sci_oxy4_oxygen' not in variables:
            self.mission_data.mission_vars.pop('sci_oxy4_oxygen')
                
        if 'sci_flbbcd_bb_units' not in variables:
            self.mission_data.mission_vars.pop('sci_flbbcd_bb_units')
        
        if 'sci_flbbcd_cdom_units' not in variables:
            self.mission_data.mission_vars.pop('sci_flbbcd_cdom_units')
            
        if 'sci_flbbcd_chlor_units' not in variables:
            self.mission_data.mission_vars.pop('sci_flbbcd_chlor_units')
                    


    def load_science(self):
        """
        Load and process science data from raw mission files.

        This method reads raw science data files, filters relevant variables,
        and computes derived quantities like salinity and density.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing processed science data.
        """
        # Load raw files from the science files location
        files = self.mission_data.get_files(files_loc=self.mission_data.sci_files_loc, extension='ebd')
        dbd = dbdreader.MultiDBD(files, cacheDir=self.mission_data.sci_cache_loc)

        # Extract variable names and filter relevant variables
        all_variables = dbd.parameterNames['sci']
        self.filter_sci_vars(all_variables)
        present_variables = ([var.data_source_name for var in self.mission_data.mission_vars.values() if var.data_source_name.startswith('sci_')])
        present_variables = set(present_variables)
        vars = dbd.get_sync(*present_variables)
        
        # Convert to a DataFrame and set column names
        self.mission_data.df_sci = pd.DataFrame(vars).T
        column_names = ['sci_m_present_time']
        column_names.extend(present_variables)
        self.mission_data.df_sci.columns = column_names

        # Convert time to datetime format and filter valid dates
        self.mission_data.df_sci['sci_m_present_time'] = pd.to_datetime(self.mission_data.df_sci['sci_m_present_time'],
                                                                        unit='s', errors='coerce')
        self.mission_data.df_sci = self.mission_data.df_sci.dropna()
        valid_dates_mask = (self.mission_data.df_sci['sci_m_present_time'] >= self.mission_data.mission_start_date) & \
                           (self.mission_data.df_sci['sci_m_present_time'] <= self.mission_data.mission_end_date)
        self.mission_data.df_sci = self.mission_data.df_sci.loc[valid_dates_mask]

        # Perform variable conversions and calculations
        self.mission_data.df_sci['sci_water_pressure'] *= 10  # Convert pressure from db to dbar
        self.mission_data.df_sci['calculated_salinity'] = gsw.SP_from_C(
            self.mission_data.df_sci['sci_water_cond'] * 10,
            self.mission_data.df_sci['sci_water_temp'],
            self.mission_data.df_sci['sci_water_pressure']
        )
        CT = gsw.CT_from_t(self.mission_data.df_sci['calculated_salinity'],
                           self.mission_data.df_sci['sci_water_temp'],
                           self.mission_data.df_sci['sci_water_pressure'])
        self.mission_data.df_sci['calculated_density'] = gsw.rho_t_exact(self.mission_data.df_sci['calculated_salinity'],
                                                                     CT,
                                                                     self.mission_data.df_sci['sci_water_pressure'])

        # Drop rows with missing values
        self.mission_data.df_sci = self.mission_data.df_sci.dropna()

        # Close the DBD reader and return the DataFrame
        dbd.close()
        return self.mission_data.df_sci


    def convert_sci_df_to_ds(self) -> xr.Dataset:
        """
        Convert the processed science DataFrame to an xarray Dataset.

        This method adds platform metadata and converts the science DataFrame into a structured xarray Dataset.

        Returns
        -------
        xr.Dataset
            The science dataset with platform metadata added.
        """
        # Add platform metadata to the dataset
        platform_ds = xr.Dataset()
        platform_ds['platform'] = xr.DataArray(self.mission_data.glider_id)
        self.mission_data.ds_sci = xr.Dataset.from_dataframe(self.mission_data.df_sci)
        self.mission_data.ds_sci = platform_ds.update(self.mission_data.ds_sci)


    def format_sci_ds(self) -> xr.Dataset:
        """
        Format the science dataset by sorting and renaming variables.

        This method organizes variables and renames them for consistency with the mission dataset's standards.

        Returns
        -------
        xr.Dataset
            The formatted science dataset.
        """
        # Sort the dataset by time and create time variable
        self.mission_data.ds_sci['index'] = np.sort(self.mission_data.ds_sci['sci_m_present_time'].values.astype('datetime64[ns]'))
        self.mission_data.ds_sci = self.mission_data.ds_sci.drop_vars('sci_m_present_time')  # Drop original time variable
        
        self.mission_data.ds_sci = self.mission_data.ds_sci.rename({'index': 'time'})


    def process_sci_data(self) -> xr.Dataset:
        """
        Perform all processing steps for science data.

        This method processes the science data from raw files to a formatted xarray Dataset,
        including variable calculations and formatting.

        Returns
        -------
        xr.Dataset
            The processed and formatted science dataset.
        """
        print_time('Processing Science Data')

        # Load science data and perform all transformations
        self.load_science()
        self.convert_sci_df_to_ds()
        self.format_sci_ds()
        print_time('Finished Processing Science Data')