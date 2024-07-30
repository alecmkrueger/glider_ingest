'''
Module containing the function to run the glider ingest process
'''
# AUTHORS:
# Alec Krueger, Texas A&M University, Geochemical and Environmental Research Group, alecmkrueger@tamu.edu
# Sakib Mahmud, Texas A&M University, Geochemical and Environmental Research Group, sakib@tamu.edu
# Xiao Ge, Texas A&M University, Geochemical and Environmental Research Group, gexiao@tamu.edu

import xarray as xr
from pathlib import Path
from processor import Processor

def process(raw_data_source:Path|str,working_directory:Path|str,glider_number:str,mission_title:str,extensions:list,output_nc_filename:str,return_ds:bool=False) -> None|xr.Dataset:
    '''
    Example Parameter inputs:

    Input information about the glider and mission for NetCDF metadata
    glider_number:str = '540'
    mission_title:str = 'Mission_44'

    Input the file extensions you would like to processs as a 1d list with the flight extension first then science
    Exammples:
    extensions = ["DBD", "EBD"]
    or 
    extensions = ["SBD", "TBD"]

    Raw data source, from the glider SD card
    raw_data_source = Path('test_data').resolve()
    Where you want the raw copy and processed data to be
    working_directory = Path('data').resolve()

    Name of the final output NetCDF file
    output_nc_filename = 2024_mission_44.nc
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

# Example:
# ds = process('540','Mission_44',extensions=['DBD','EBD'],raw_data_source=Path('../../test_data').resolve(),
#              working_directory=Path('../../data').resolve(),output_nc_filename='test.nc',return_ds=True)



