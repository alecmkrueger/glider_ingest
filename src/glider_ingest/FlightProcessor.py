import numpy as np
import pandas as pd
import xarray as xr
import dbdreader
from attrs import define

from glider_ingest.MissionData import MissionData
from glider_ingest.variable import Variable
from glider_ingest.utils import print_time


@define
class FlightProcessor:
    """
    A class to process flight data from gliders.
    
    The data is loaded from DBD files, converted to pandas DataFrames, and then 
    transformed into xarray Datasets with metadata attributes.

    Parameters
    ----------
    mission_data : MissionData
        An instance of the MissionData class containing mission information.
    """
    
    mission_data: MissionData

    def load_flight(self):
        """
        Load flight data from DBD files and preprocess the data.

        Loads and processes flight data through the following steps:
        - Loads data using the DBDReader package
        - Filters data within the mission start and end dates
        - Converts pressure from decibars to bars
        - Renames latitude and longitude columns for clarity
        """
        files = self.mission_data.get_files(files_loc=self.mission_data.fli_files_loc, extension='dbd')
        dbd = dbdreader.MultiDBD(files, cacheDir=self.mission_data.fli_cache_loc)        
        get_vars = ([var.data_source_name for var in self.mission_data.mission_vars.values() if var.data_source_name.startswith('m_')])
        data = dbd.get_sync(*get_vars)
        
        self.mission_data.df_fli = pd.DataFrame(data).T
        new_column_names = ['m_present_time']
        new_column_names.extend(get_vars)
        self.mission_data.df_fli.columns = new_column_names
        self.mission_data.df_fli['m_present_time'] = pd.to_datetime(self.mission_data.df_fli['m_present_time'], unit='s')

        # Remove data with erroneous dates
        self.mission_data.df_fli = self.mission_data.df_fli.loc[
            (self.mission_data.df_fli['m_present_time'] > self.mission_data.mission_start_date) &
            (self.mission_data.df_fli['m_present_time'] < self.mission_data.mission_end_date)
        ]
        
        # Convert pressure from decibar to bar
        self.mission_data.df_fli['m_pressure'] *= 10

        # Rename columns for clarity and remove NaN values
        self.mission_data.df_fli = self.mission_data.df_fli.dropna()
        dbd.close()


    def convert_fli_df_to_ds(self) -> xr.Dataset:
        """
        Convert the flight DataFrame to an xarray Dataset and store it in MissionData.

        Returns:
            xr.Dataset: The converted Dataset from the flight DataFrame.
        """
        self.mission_data.ds_fli = xr.Dataset.from_dataframe(self.mission_data.df_fli)


    def format_flight_ds(self) -> xr.Dataset:
        """
        Format the flight Dataset.

        Performs the following operations:
        - Sorts the Dataset based on present time
        - Drops the original time variable
        - Renames relevant variables

        Returns
        -------
        xr.Dataset
            The formatted flight Dataset.
        """
        self.mission_data.ds_fli['index'] = np.sort(self.mission_data.ds_fli['m_present_time'].values.astype('datetime64[ns]'))
        self.mission_data.ds_fli = self.mission_data.ds_fli.drop_vars('m_present_time')
        self.mission_data.ds_fli = self.mission_data.ds_fli.rename({'index': 'm_time'})

        # self.mission_data.ds_fli = self.mission_data.ds_fli.rename({'index': 'm_time','m_pressure':'m_pressure','m_water_depth':'depth','m_latitude':'latitude','m_longitude':'longitude'})


    def process_flight_data(self) -> xr.Dataset:
        """
        Execute the complete flight data processing pipeline.

        Performs the following steps:
        1. Load flight data from DBD files
        2. Convert DataFrame to Dataset
        3. Add metadata attributes
        4. Format the Dataset

        Returns
        -------
        xr.Dataset
            The final processed flight Dataset.
        """
        print_time('Processing Flight Data')
        self.load_flight()
        self.convert_fli_df_to_ds()
        self.format_flight_ds()
        print_time('Finised Processing Flight Data')
