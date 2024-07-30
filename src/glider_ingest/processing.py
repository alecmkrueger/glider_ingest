# AUTHORS:
# Alec Krueger, Texas A&M University, Geochemical and Environmental Research Group, alecmkrueger@tamu.edu
# Sakib Mahmud, Texas A&M University, Geochemical and Environmental Research Group, sakib@tamu.edu
# Xiao Ge, Texas A&M University, Geochemical and Environmental Research Group, gexiao@tamu.edu

import xarray as xr
from pathlib import Path
from processor import Processor
# from utils import delete_files_in_directory,create_directory,copy_raw_data,rename_binary_files
# from utils import convert_binary_to_ascii,convert_ascii_to_dataset,save_ds

def process(glider_number:str,mission_title:str,extensions:list,raw_data_source:Path,working_directory:Path,output_nc_filename:str,return_ds:bool=False) -> None|xr.Dataset:
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
    raw_data_source = Path('../../test_data').resolve()
    Where you want the raw copy and processed data to be
    working_directory = Path('data').resolve()

    Name of the final output NetCDF file
    output_nc_filename = 2024_mission_44.nc
    '''
    processor = Processor(raw_data_source=raw_data_source,working_directory=working_directory,glider_number=glider_number,
                          mission_title=mission_title,output_nc_filename=output_nc_filename,extensions=extensions)
    processor.process()

    if return_ds:
        return processor.ds_mission

ds = process('540','Mission_44',extensions=['DBD','EBD'],raw_data_source=Path('../../test_data').resolve(),
             working_directory=Path('../../data').resolve(),output_nc_filename='test.nc',return_ds=True)



