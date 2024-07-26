# processing.py

# AUTHORS:
# Sakib Mahmud, Texas A&M University, Geochemical and Environmental Research Group, sakib@tamu.edu
# Xiao Ge, Texas A&M University, Geochemical and Environmental Research Group, gexiao@tamu.edu
# Alec Krueger, Texas A&M University, Geochemical and Environmental Research Group, alecmkrueger@tamu.edu

import xarray as xr
from pathlib import Path
from utils import delete_files_in_directory,create_directory,copy_raw_data,rename_dbd_ebd_files
from utils import convert_dbd_ebd_to_ascii,convert_ascii_to_dataset,save_ds

def process(glider_number:str,mission_title:str,raw_data_source:Path,working_directory:Path,output_nc_filename:str,return_ds:bool=False) -> None|xr.Dataset:
	'''
	Example Parameter inputs:
	
	Input information about the glider and mission for NetCDF metadata
	glider_number:str = '540'
	mission_title:str = 'Mission_44'

	Raw data source, from the glider SD card
	raw_data_source = Path('../../test_data').resolve()
	Where you want the raw copy and processed data to be
	working_directory = Path('data').resolve()

	Name of the final output NetCDF file
	output_nc_filename = 2024_mission_44.nc
	'''
	
	# Create/verify directory structure
	create_directory(working_directory)

	# Ensure a clean data working directory
	delete_files_in_directory(working_directory)

	# Copy over raw data from glider into the working directory
	copy_raw_data(input_data_dir=raw_data_source, working_directory=working_directory, max_workers=8)

	# Use rename_dbd_files.exe to add metadata from the dbd and ebd files to their filenames
	rename_dbd_ebd_files(working_directory=working_directory, max_workers=8)

	# Use dbd2asc.exe to convert the binary dbd and ebd files to ascii files
	convert_dbd_ebd_to_ascii(working_directory=working_directory, max_workers=8)

	# Combine all ascii files into a single NetCDF with gridded data
	ds_mission = convert_ascii_to_dataset(working_directory=working_directory, glider=glider_number, 
						          mission_title=mission_title)
	
	# Save the dataset
	save_ds(ds_mission=ds_mission,output_nc_path=working_directory.joinpath('processed','nc',output_nc_filename))	

	if return_ds:
		return ds_mission
	else:
		return None

