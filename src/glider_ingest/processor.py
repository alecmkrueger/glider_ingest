'''
Module containing the Processor class
'''
from attrs import define,field
import xarray as xr
import numpy as np
from pathlib import Path
import os
from collections import Counter
import multiprocessing
from concurrent.futures import ThreadPoolExecutor,as_completed
import platform
import datetime

from .utils import print_time,copy_file,rename_file,create_tasks,convert_file,clean_dir
from .utils import process_sci_data,process_flight_data,add_gridded_data,add_global_attrs,length_validator

@define
class Processor:
    '''Class to process and contain information about the raw glider data ingest'''
    raw_data_source:Path
    working_directory:Path
    mission_number:str

    mission_title:str = field(default=None)
    output_nc_filename:str = field(default=None)
    glider_number:str = field(default=None)
    mission_start_date:str = field(default='2012-01-01')
    extensions:list = field(default=['DBD','EBD'],validator=length_validator)
    data_sources:list = field(default=['Flight', 'Science'],validator=length_validator)
    glider_id:dict = field(default={'199':'Dora','307':'Reveille','308':'Howdy','540':'Stommel','541':'Sverdrup'})
    wmo_id:dict = field(default={'199':'unknown','307':'4801938','308':'4801915','540':'4801916','541':'4801924'})
    mission_year:int = field(default=None)
    max_workers:int|None = field(default=None)
    debug:bool = field(default=False)
    skip_confirmation:bool = field(default=False)

    ds_mission:xr.Dataset = field(init=False)
    output_nc_path:Path = field(init=False)
    package_dir:Path = field(init=False)
    rename_exe_path:Path = field(init=False)
    binary2asc_exe_path:Path = field(init=False)
    cache_dir:Path = field(init=False)


    def __attrs_post_init__(self):
        self.package_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.working_directory = self.working_directory.joinpath(f"Mission_{self.mission_number}")
        if self.max_workers is None:
            self.max_workers = multiprocessing.cpu_count()
        self.pick_executables()

    def pick_executables(self):
        current_os = platform.system()
        if current_os == 'Linux' or current_os == 'Darwin':
            self.rename_exe_path = self.package_dir.joinpath('rename_files.exe')
            self.binary2asc_exe_path = self.package_dir.joinpath('binary2asc.exe')
        elif current_os == 'Windows':
            self.rename_exe_path = self.package_dir.joinpath('windows_rename_files.exe')
            self.binary2asc_exe_path = self.package_dir.joinpath('windows_binary2asc.exe')
        else:
            required_os_list = ['Windows','Linux','Darwin']
            raise ValueError(f"Unknown Operating System, got {current_os}, must be one of {required_os_list}")

    def print_time_debug(self,message):
        # Print the message if self.debug is true
        if self.debug:
            print_time(message)

    def create_directory(self):
        '''
        Create the directory that will contain the raw and processed data inside the user defined working directory
        Sets up the structure that the rest of the module uses to put the data in the correct spots
        '''
        self.print_time_debug(f'Creating Directory at {self.working_directory}')
        # Create cache dir
        self.cache_dir = self.package_dir.joinpath('cache')
        self.cache_dir.mkdir(exist_ok=True)
        # Define the two data type folders
        data_types = ['processed','raw_copy']
        # Define the three processed folders
        processed_data_types = ['Flight','nc','Science']
        # Define the raw data type folders by the file extension of the files to be stored
        raw_flight_extensions = ["DBD", "MBD", "SBD", "MLG"]
        raw_science_extensions = ["EBD", "NLG", "TBD", "NBD"]
        # Loop through the two data type folders
        for dtype in data_types:
            if dtype == 'processed':
                for processed_dtype in processed_data_types:
                    # Example directory being created: self.working_directory/processed/Flight
                    # os.makedirs(self.working_directory.joinpath(dtype, processed_dtype), exist_ok=True)
                    self.working_directory.joinpath(dtype, processed_dtype).mkdir(exist_ok=True,parents=True)
            elif dtype == 'raw_copy':
                # Package Flight and Science with their respective data type folders (extensions)
                for data_source,extensions in zip(['Flight','Science'],[raw_flight_extensions,raw_science_extensions]):
                    for extension in extensions:
                        # Example directory being created: self.working_directory/raw_copy/Flight/DBD
                        # os.makedirs(self.working_directory.joinpath(dtype ,data_source, extension), exist_ok=True)
                        self.working_directory.joinpath(dtype ,data_source, extension).mkdir(exist_ok=True,parents=True)
        self.print_time_debug('Finished Creating Directory')

    def delete_files_in_directory(self):
        '''
        Clean up the directory incase there are files that already exist.
        If you do not delete the files in the directory before running the rest of the script,
        then there will likely be data duplication and errors.
        So to be save, always clean up the directory using this function
        '''
        self.print_time_debug('Deleting Files')
        if self.skip_confirmation:
            confirmation = 'yes'
        else:
            # Check if the user wishes to delete all files in the directory
            confirmation = input(f"Are you sure you want to delete all files in '{self.working_directory}' and its subdirectories? Type 'yes' to confirm, 'no' to continue without deleting files, press escape to cancel and end ")
        # If so then begin finding files
        if confirmation.lower() == 'yes':
            # clear cache
            # cache_path = Path('cache').resolve()
            [os.remove(file) for file in self.cache_dir.rglob('*.cac')]
            # clear all files in the given directory
            for root, _, files in os.walk(self.working_directory):
                file_count = len(files)
                for file in files:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
                if file_count > 0:
                    self.print_time_debug(f"Cleaned {root}, deleted {file_count} file(s).")
            self.print_time_debug("All files have been deleted")
        elif confirmation.lower() == 'no':
            self.print_time_debug('Continuing without deleting files, this may cause unexpected behaviours including data duplication')
        else:
            raise ValueError("Cancelling: If you did not press escape, ensure you type 'yes' or 'no'. ")   
        self.print_time_debug('Finished Deleting Files')

    def copy_raw_data(self):
        '''
        Copy data from the memory card to the working directory using multithreading.
        We only work on the copied data and never the source data
        '''
        self.print_time_debug('Copying Raw files')
        if self.skip_confirmation:
            confirmation = 'yes'
        else:
            confirmation = input(f"Do you want to copy files from '{self.raw_data_source}' to '{self.working_directory}'? Type 'yes' to confirm, 'no' to continue without deleting files, press escape to cancel and end ")
        # If so then begin finding files
        if confirmation.lower() == 'yes':
            raw_output_data_dir = self.working_directory.joinpath('raw_copy')

            all_extensions = [["DBD", "MBD", "SBD", "MLG", "CAC"], ["EBD", "NLG", "TBD", "NBD", "CAC"]]
            
            tasks = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                for data_source, extensions in zip(self.data_sources, all_extensions):
                    input_data_path = self.raw_data_source.joinpath(f'{data_source}_card')
                    for file_extension in extensions:
                        # If the extension is CAC then we want to copy the files to the cache folder
                        if file_extension == 'CAC':
                            # Add cache to internal cache folder
                            output_data_path = self.cache_dir
                        else:
                            output_data_path = raw_output_data_dir.joinpath(data_source, file_extension)
                        # Find all of the files with the file extension 
                        input_files = input_data_path.rglob(f'*.{file_extension}')
                        # Loop through the files with matching extensions
                        for input_file_path in input_files:
                            # Define where the file will be placed
                            output_file_path = output_data_path.joinpath(input_file_path.name)
                            # Append the input and output file paths to a list
                            tasks.append((input_file_path, output_file_path))
                # Queue the copy_file function using multiprocessing on the input and output file paths
                futures = [executor.submit(copy_file, input_file_path, output_file_path) for input_file_path, output_file_path in tasks]
                # Perform the multiprocessing
                for future in as_completed(futures):
                    try:
                        future.result()  # Raise any exceptions that occurred
                    except Exception as e:
                        self.print_time_debug(f"Error copying file: {e}")
        elif confirmation.lower() == 'no':
            self.print_time_debug('Continuing without deleting files, this may cause unexpected behaviours including data duplication')
        else:
            raise ValueError("Cancelling: If you did not press escape, ensure you type 'yes' or 'no'.") 
        self.print_time_debug('Done Copying Raw files')

    def rename_binary_files(self):
        '''Rename files to contain date and glider name in the input data directory using multithreading.'''
        self.print_time_debug('Renaming files')
        
        raw_copy_directory = self.working_directory.joinpath('raw_copy')

        tasks = []
        for extension in self.extensions:
            data_files = list(raw_copy_directory.rglob(f'*.{extension}'))
            tasks.extend(data_files)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(rename_file, self.rename_exe_path, file) for file in tasks]
            
            for future in as_completed(futures):
                try:
                    future.result()  # Raise any exceptions that occurred
                except Exception as e:
                    self.print_time_debug(f"Error renaming file: {e}")

        self.print_time_debug("Done renaming files")

    def get_glider_number(self):
        """
        Determines the most frequent valid instrument name in the first 10 files,
        provided it appears at least 4 times. Returns the valid instrument name.
        
        return: The valid instrument name or None if no valid name is found
        """
        # If the glider number is supplied by user, do not try to find it
        if self.glider_number is None:
            def extract_instrument_name(filename, instrument_dict):
                # Check for instrument names in filename
                for key, value in instrument_dict.items():
                    if key in filename or value in filename:
                        return key if key in filename else value
                return None

            # Get the first 10 files from the folder
            raw_copy_directory = self.working_directory.joinpath('raw_copy')
            
            # Get the first 10 files from the folder with the desired extensions
            files = list(raw_copy_directory.rglob('*dbd'))[10:20]

            # Count occurrences of instrument names in files
            instrument_counter = Counter()
            for file in files:
                instrument_name = extract_instrument_name(file.name, self.glider_id)
                if instrument_name:
                    instrument_counter[instrument_name] += 1

            # Find the instrument name with the highest count
            if instrument_counter:
                most_common_instrument, count = instrument_counter.most_common(1)[0]
                
                self.glider_number = most_common_instrument
            
            if self.glider_number is None:
                # Return None if no valid instrument is found
                raise ValueError('Could not find the glider number, please provide the glider number')
        
    def get_mission_year(self):
        if self.mission_start_date != '2012-01-01':
            self.mission_year = datetime.datetime.strptime(self.mission_start_date, "%Y-%m-%d").date().year
        else:
            raw_copy_directory = self.working_directory.joinpath('raw_copy')
            file = list(raw_copy_directory.rglob('*dbd'))[30]
            file = file.stem
            year_loc = file.find('-')+1
            mission_year = file[year_loc:year_loc+4]
            self.mission_year = mission_year

    def make_mission_title(self):
        if self.mission_title is None:
            ''''''
            self.mission_title = f'Mission_{self.mission_number}_{self.glider_number}'

    def make_output_nc_filename(self):
        if self.output_nc_filename is None:
            self.output_nc_filename = f'M{self.mission_number}_{self.mission_year}_{self.glider_number}.nc'
        self.output_nc_path = self.working_directory.joinpath('processed','nc',self.output_nc_filename)

    def convert_binary_to_ascii(self):
        '''Converts binary files to ascii in the input directory and saves them to the output directory'''
        
        working_dir = os.getcwd()
        os.chdir(str(self.package_dir))
        self.print_time_debug('Converting to ascii')
        output_data_dir = self.working_directory.joinpath('processed')
        working_directory = self.working_directory.joinpath('raw_copy')
        
        # Collect all files to be processed
        tasks = []
        for data_source, extension in zip(self.data_sources, self.extensions):
            tasks = create_tasks(working_directory,data_source,extension,output_data_dir,tasks,self.binary2asc_exe_path)
        
        # Process files in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(convert_file, binary2asc_path, raw_file, ascii_file) for binary2asc_path, raw_file, ascii_file in tasks]
            for future in as_completed(futures):
                future.result()  # Raise any exceptions that occurred
        
        os.chdir(working_dir)
        self.print_time_debug('Done Converting to ascii')

    def convert_ascii_to_dataset(self):
        '''Convert ascii data files into a single NetCDF file'''
        self.print_time_debug('Converting ascii to dataset')
        processed_directory = self.working_directory.joinpath('processed')

        science_data_dir:Path = processed_directory.joinpath('Science')
        flight_data_dir:Path = processed_directory.joinpath('Flight')
        
        # Process Science Data
        ds_sci:xr.Dataset = process_sci_data(science_data_dir,self.glider_id,self.glider_number,self.wmo_id,mission_start_date=self.mission_start_date)

        # Make a copy of the science dataset
        ds_mission:xr.Dataset = ds_sci.copy()

        # Process Flight Data
        ds_fli:xr.Dataset = process_flight_data(flight_data_dir,mission_start_date=self.mission_start_date)

        # Add flight data to mission dataset
        ds_mission.update(ds_fli)

        # Add gridded data to mission dataset
        ds_mission = add_gridded_data(ds_mission)

        # Add attributes to the mission dataset
        self.ds_mission = add_global_attrs(ds_mission,mission_title=self.mission_title,wmo_id=self.wmo_id,glider=self.glider_number)

        self.print_time_debug('Finished converting ascii to dataset')

    def save_ds(self):
        '''Save the mission dataset to NetCDF'''
        self.print_time_debug(f'Saving dataset to {self.output_nc_path}')
        self.ds_mission.to_netcdf(self.output_nc_path,engine='netcdf4')
        self.print_time_debug('Finished saving dataset')

    def remove_temp_files(self):
        raw_files_directory = self.working_directory.joinpath('raw')
        flight_directory = self.working_directory.joinpath('processed','Flight')
        science_directory = self.working_directory.joinpath('processed','Science')
        clean_dir(raw_files_directory)
        clean_dir(flight_directory)
        clean_dir(science_directory)


    def process(self,remove_temp_files:bool=False):
        '''Perform the processing of the raw glider data into a NetCDF file'''
        self.create_directory()
        self.delete_files_in_directory()
        self.copy_raw_data()
        self.rename_binary_files()
        self.get_mission_year()
        self.get_glider_number()
        self.make_mission_title()
        self.make_output_nc_filename()
        self.convert_binary_to_ascii()
        self.convert_ascii_to_dataset()
        self.save_ds()
        if remove_temp_files:
            self.remove_temp_files()
