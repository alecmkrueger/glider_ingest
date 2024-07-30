'''
Module containing the function to run the glider ingest process
'''
# AUTHORS:
# Alec Krueger, Texas A&M University, Geochemical and Environmental Research Group, alecmkrueger@tamu.edu
# Sakib Mahmud, Texas A&M University, Geochemical and Environmental Research Group, sakib@tamu.edu
# Xiao Ge, Texas A&M University, Geochemical and Environmental Research Group, gexiao@tamu.edu

import xarray as xr
from pathlib import Path
from .processor import Processor

def process(raw_data_source:Path|str,working_directory:Path|str,glider_number:str,mission_title:str,extensions:list,output_nc_filename:str,return_ds:bool=False) -> None|xr.Dataset:
    '''

    Function inputs:
    * raw_data_source (Path|str): Raw data source, from the glider SD card
    * working_directory (Path|str): Where you want the raw copy and processed data to be
    * glider_number (str): The number of the glider, for NetCDF metadata
    * mission_title (str): The mission title, for NetCDF metadata
    * extensions (list): The extensions you wish to process
    * output_nc_filename (str): The name of the output NetCDF file
    * return_ds (bool): If you would like the output dataset to be returned. Default = False

    Example Parameter inputs:
    * glider_number:str = '540'
    * mission_title:str = 'Mission_44'
    * extensions = ["DBD", "EBD"] or ["SBD", "TBD"]
    * raw_data_source = Path('test_data').resolve()
    * working_directory = Path('data').resolve()
    * output_nc_filename = 2024_mission_44.nc
    * return_ds = True
    '''
    if isinstance(raw_data_source,str):
        raw_data_source = Path(raw_data_source)
    if isinstance(working_directory,str):
        working_directory = Path(working_directory)

    if not raw_data_source.exists():
        raise ValueError(f'Raw data source directory does not exist: {raw_data_source}')

    if not working_directory.exists():
        raise ValueError(f'Working directory does not exist: {working_directory}')
    
    processor = Processor(raw_data_source=raw_data_source,working_directory=working_directory,glider_number=glider_number,
                          mission_title=mission_title,output_nc_filename=output_nc_filename,extensions=extensions)
    processor.process()

    if return_ds:
        return processor.ds_mission





