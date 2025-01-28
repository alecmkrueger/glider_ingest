import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from attrs import define, field
import datetime
import dbdreader
import shutil
import gsw
import time
import random
import os

from glider_ingest.utils import get_polygon_coords,print_time,find_nth
from glider_ingest.variable import Variable
from glider_ingest.gridder import Gridder
from glider_ingest.dataset_attrs import get_default_variables, get_global_attrs


@define
class Processor:
    """
    A class to process glider data
    """
    # Required attributes
    memory_card_copy_path: Path
    working_dir: Path
    mission_num: str
    # Default attributes
    mission_vars: list[Variable] = field(factory=list)
    glider_ids: dict = field(default={'199': 'Dora', '307': 'Reveille', '308': 'Howdy', '540': 'Stommel', '541': 'Sverdrup', '1148': 'unit_1148'})
    wmo_ids: dict = field(default={'199': 'unknown', '307': '4801938', '308': '4801915', '540': '4801916', '541': '4801924', '1148': '4801915'})
    
    # Optional attributes
    mission_start_date: datetime.datetime = field(default=pd.to_datetime('2010-01-01'))  # Used to slice the data during processing
    mission_end_date: datetime.datetime = field(default=pd.to_datetime(datetime.datetime.today()+datetime.timedelta(days=365)))  # Used to slice the data during processing
    
    # Created attributes
    df: pd.DataFrame = field(default=None)
    ds: xr.Dataset = field(default=None)
    
    # Private backing fields
    _glider_id: str = field(default=None)
    _glider_name: str = field(default=None)
    _wmo_id: str = field(default=None)
    _mission_year: str = field(default=None)
    _mission_title: str = field(default=None)
    _mission_folder_name: str = field(default=None)
    _mission_folder_path: Path = field(default=None)
    _netcdf_filename: str = field(default=None)
    _netcdf_output_path: Path = field(default=None)

    @property
    def glider_id(self):
        """Get the glider ID."""
        if self._glider_id is None:
            self._glider_id = self._get_glider_id()
        return self._glider_id

    @property
    def glider_name(self):
        """Get the glider name."""
        if self._glider_name is None:
            self._glider_name = self.glider_ids[self.glider_id]
        return self._glider_name

    @property
    def wmo_id(self):
        """Get the WMO ID."""
        if self._wmo_id is None:
            self._wmo_id = self.wmo_ids[self.glider_id]
        return self._wmo_id
    
    @property
    def mission_year(self):
        """Get the mission year."""
        if self._mission_year is None:
            self._mission_year = self._get_mission_year()
        return self._mission_year

    @property
    def mission_title(self):
        """Get the mission title."""
        if self._mission_title is None:
            self._mission_title = f'Mission {self.mission_num}'
        return self._mission_title

    @property
    def mission_folder_name(self):
        """Get the mission folder name."""
        if self._mission_folder_name is None:
            self._mission_folder_name = self.mission_title.replace(' ', '_')
        return self._mission_folder_name

    @property
    def mission_folder_path(self):
        """Get the mission folder path."""
        if self._mission_folder_path is None:
            self._mission_folder_path = self.working_dir.joinpath(self.mission_folder_name)
        return self._mission_folder_path

    @property
    def netcdf_filename(self):
        """Get the NetCDF filename."""
        if self._netcdf_filename is None:
            self._netcdf_filename = f'M{self.mission_num}_{self.mission_year}_{self.glider_id}.nc'
        return self._netcdf_filename

    @property
    def netcdf_output_path(self):
        """Get the NetCDF path."""
        if self._netcdf_output_path is None:
            self._netcdf_output_path = self.mission_folder_path.joinpath(f'{self.netcdf_filename}')
        return self._netcdf_output_path

    
    def __attrs_post_init__(self):
        """
        Post init method to add default variables to the mission_vars list
        """
        self.add_mission_vars(get_default_variables())
        
        
    def _check_mission_var_duplicates(self):
        """
        Check for duplicate variables in the mission_vars list
        """
        # Get the variable data_source_names
        var_names = self._get_mission_variable_short_names()
        if len(set(var_names)) != len(var_names):
            print('Duplicate variables in mission_vars list')
        
    def add_mission_vars(self, mission_vars: list[Variable]):
        """
        Add a variable to the mission_vars list
        """
        if all(isinstance(var, str) for var in mission_vars):
            mission_vars = [Variable(data_source_name=var) for var in mission_vars]
        self.mission_vars.extend(mission_vars)
        self._check_mission_var_duplicates()
        
   
    def _copy_files(self):
        """
        Copy only LOGS and STATE/CACHE folders from memory card copy to working directory
        """
        original_loc = self.memory_card_copy_path
        new_loc = self.mission_folder_path
        
        # Define patterns to include
        include_patterns = ['**/LOGS', '**/logs', '**/STATE/CACHE', '**/state/cache']
        
        for pattern in include_patterns:
            for source_path in original_loc.glob(pattern):
                # Create relative path to maintain directory structure
                relative_path = source_path.relative_to(original_loc)
                destination_path = new_loc / relative_path
                
                # Create parent directories if they don't exist
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy directory
                if source_path.is_dir():
                    shutil.copytree(source_path, destination_path, dirs_exist_ok=True)


    def _get_files_by_extension(self,directory_path: Path, extensions: list[str], as_string: bool = False) -> list:
        """
        Get files from a directory with specified extensions.

        Args:
            directory_path (Path): Directory to search for files
            extensions (list[str]): List of file extensions to match (e.g. ['.dbd', '.DBD'])
            as_string (bool): Whether to return paths as strings

        Returns:
            list: List of matching files as Path objects or strings
        """
        files = [p for p in directory_path.rglob('*') if p.suffix in extensions]
        if as_string:
            files = [str(p) for p in files]
        return files
        
    def _get_cache_files(self,as_string:bool=False):
        """
        Get the cache files from the memory card copy
        """
        extensions = ['.cac','.CAC']
        directory_path = self.mission_folder_path
        cac_files = self._get_files_by_extension(directory_path=directory_path,extensions=extensions,as_string=as_string)
        return cac_files

    def _get_cache_files_path(self):
        """
        Get the cache file path from the memory card copy
        """
        return self.mission_folder_path.joinpath('cache')

    def _copy_cache_files(self):
        """
        Move the cache files to the working directory
        """
        cache_files = self._get_cache_files()
        new_cache_loc = self._get_cache_files_path()
        if not new_cache_loc.exists():
            new_cache_loc.mkdir()
        for cache_file in cache_files:
            # check if cache file already exists
            if new_cache_loc.joinpath(cache_file.name).exists():
                continue
            # copy cache file
            new_cache_filename = new_cache_loc.joinpath(cache_file.name)
            print(f'Coping {cache_file} to {new_cache_loc}')
            shutil.copy2(cache_file, new_cache_filename)
            
    def _get_dbd_files(self,as_string=False):
        """
        Get the dbd files from the memory card copy
        """
        directory_path = self.mission_folder_path
        extensions = ['.dbd','.DBD','.ebd','.EBD']
        dbd_files = self._get_files_by_extension(directory_path=directory_path,extensions=extensions,as_string=as_string)
        return dbd_files
        
    def _read_dbd(self):
        """
        Read the files from the memory card copy
        """
        self._copy_files()
        time.sleep(2)
        self._copy_cache_files()
        
        filenames = self._get_dbd_files(as_string=True)
        dbd = dbdreader.MultiDBD(filenames=filenames,cacheDir=self._get_cache_files_path())
        return dbd
    
    def _get_dbd_variables(self,dbd,sci_vars=True,eng_vars=True) -> list:
        """
        Get the dbd variables from the files. Returns both sci and eng if both are true.
        
        If sci_vars and eng_vars are both False, raise a ValueError
        
        
        Parameters
        ----------
        sci_vars : bool, optional
        Whether to include science variables, default: True
        eng_vars : bool, optional
        Whether to include engineering variables, default: True
        
        Returns
        -------
        list
        
        Raises
        ------
        ValueError
        If sci_vars and eng_vars are both False
        """
        sci_dbd_vars = dbd.parameterNames['sci']
        eng_dbd_vars = dbd.parameterNames['eng']
        all_dbd_vars = sci_dbd_vars + eng_dbd_vars
        if sci_vars and not eng_vars:
            return sci_dbd_vars
        elif eng_vars and not sci_vars:
            return eng_dbd_vars
        elif sci_vars and eng_vars:
            return all_dbd_vars
        else:
            raise ValueError('Must specify sci_vars and/or eng_vars')
    
    def _get_mission_variables(self,filter_out_none=False):
        """
        Get the mission variables from the mission_vars list. Filter out None data_source_name values if desired.
        """
        if filter_out_none:
            return [var for var in self.mission_vars if var.data_source_name is not None]
        else:
            return self.mission_vars
    
    def _get_mission_variable_short_names(self,filter_out_none=False):
        """
        Get the mission variable data source names from the mission_vars list
        """
        return [var.short_name for var in self._get_mission_variables(filter_out_none=filter_out_none)]
    
    def _get_mission_variable_data_source_names(self,filter_out_none=False):
        """
        Get the mission variable data source names from the mission_vars list
        """
        return [var.data_source_name for var in self._get_mission_variables(filter_out_none=filter_out_none)]
    
    def _check_default_variables(self,dbd,variables_to_get:list):
        """
        Check that the default variables are in the dbd variables
        """
        dbd_vars = self._get_dbd_variables(dbd=dbd)
        missing_vars = [var for var in variables_to_get if var not in dbd_vars]
        if missing_vars:
            print(f'The following variables are missing from the dbd files: {missing_vars}')
        
    def _get_sci_files(self):
        """
        Get the sci files from the memory card copy
        """
        directory_path = self.mission_folder_path
        extensions = ['.dbd','.DBD']
        sci_files = self._get_files_by_extension(directory_path=directory_path,extensions=extensions,as_string=True)
        return sci_files
        
    def _get_random_sci_file(self):
        """
        Get a random sci file from the mission folder
        """
        sci_files = self._get_sci_files()
        random_file = random.choice(sci_files)
        # Pick a new file if the file is empty
        while os.stat(random_file).st_size == 0:
            random_file = random.choice(sci_files)
        return random_file
        
    def _get_full_filename(self):
        """
        Get the full filename from the file
        Args:
            file (str): Path to the file to read.

        Returns:
            str: The extracted full filename, or None if not found.
        """
        file = self._get_random_sci_file()
        with open(file, errors="ignore") as fp:
            for line in fp:
                if 'full_filename' in line.strip():
                    return line.replace('full_filename:', '').strip()
        return None
    
    def _get_mission_year(self):
        """
        Get the mission year from the filename.

        Extracts and validates the mission year from the filename, converting between
        mission names and IDs as needed using the mission_ids mapping.

        Returns
        -------
        str
            The validated mission year
        """
        full_filename = self._get_full_filename()
        mission_year = full_filename[full_filename.find('-') + 1: find_nth(full_filename, '-', 2)].strip()
        return mission_year
        
    def _get_glider_id(self):
        """
        Get the glider id from the filename.
        
        Extracts and validates the glider identifier from the filename, converting between
        glider names and IDs as needed using the glider_ids mapping.
        
        Returns
        -------
        str
            The validated glider ID
        """
        full_filename = self._get_full_filename()
        glider_identifier = full_filename.split('-')[0].replace('unit_', '').strip()
        
        # Create reverse mapping from names to IDs
        inverted_glider_ids = {v: k for k, v in self.glider_ids.items()}
        
        # Check if identifier is a valid ID
        if glider_identifier in self.glider_ids:
            return glider_identifier
            
        # Check if identifier is a valid name
        if glider_identifier in inverted_glider_ids:
            return inverted_glider_ids[glider_identifier]
            
        valid_options = list(self.glider_ids.keys()) + list(self.glider_ids.values())
        print(f'Invalid glider identifier: {glider_identifier}. Must be one of: {valid_options}')
        return None
    
    def _get_dbd_data(self):
        dbd = self._read_dbd()
        variables_to_get = self._get_mission_variable_data_source_names(filter_out_none=True)
        self._check_default_variables(dbd,variables_to_get)
        data = dbd.get_sync(*variables_to_get)
        dbd.close()
        return data
    
    def _format_time(self,df:pd.DataFrame):
        # Convert time to datetime format and filter valid dates
        df['time'] = pd.to_datetime(df['time'],unit='s', errors='coerce')
        df = df.dropna(how='all')
        valid_dates_mask = (df['time'] >= self.mission_start_date) & \
                           (df['time'] <= self.mission_end_date)
        df = df.loc[valid_dates_mask]
        return df
        
    def _calculate_vars(self,df):
        # Perform variable conversions and calculations
        df['m_pressure'] *= 10  # Convert pressure from db to dbar
        df['sci_water_pressure'] *= 10  # Convert pressure from db to dbar
        df['salinity'] = gsw.SP_from_C(df['sci_water_cond'] * 10, df['sci_water_temp'], df['sci_water_pressure'])
        CT = gsw.CT_from_t(df['salinity'], df['sci_water_temp'], df['sci_water_pressure'])
        df['density'] = gsw.rho_t_exact(df['salinity'], CT, df['sci_water_pressure'])
        return df
    
    def _update_dataframe_columns(self,df):
        """
        Update the dataframe columns with the mission variables.
        Adjusting the current column names, which are data source names, to their short_name values.
        """
        column_map = {value.data_source_name: value.short_name for value in self.mission_vars}
        df = df.rename(columns=column_map)
        return df
    
    def _convert_dbd_to_dataframe(self):
        """
        Get the dbd data as a dataframe
        """
        data = self._get_dbd_data()
        df = pd.DataFrame(data).T
        new_column_names = ['time']
        new_column_names.extend(self._get_mission_variable_data_source_names(filter_out_none=True))
        if len(df.columns) != len(new_column_names):
            print(f'The number of columns in the dataframe does not match the number of mission variables, {df.columns} vs {new_column_names}')
        # Add names to the dataframe columns
        df.columns = new_column_names
        # Format time
        df = self._format_time(df)
        # Calculate variables
        df = self._calculate_vars(df)
        # Set time as index
        df = df.set_index('time')
        df = self._update_dataframe_columns(df)
        self.df = df
        return self.df
    
    def _convert_df_to_ds(self):
        df = self._convert_dbd_to_dataframe()
        ds = xr.Dataset.from_dataframe(df)
        self.ds = ds
        return self.ds
    
    def _get_longitude(self):
        return self.ds.longitude.values
    
    def _get_latitude(self):
        return self.ds.latitude.values
    
    def _get_depth(self):
        return self.ds.depth.values
    
    def _get_time(self):
        return self.ds.time.values

    def _add_global_attrs(self):
        from glider_ingest.dataset_attrs import get_global_attrs
        global_attrs = get_global_attrs(wmo_id = self.wmo_id,mission_title=self.mission_title,
                                        longitude=self._get_longitude(),latitude=self._get_latitude(),
                                        depth=self._get_depth(),time=self._get_time())
        
        self.ds.attrs = global_attrs                                        
        
    def _add_variable_attrs(self):
        for var in self.mission_vars:
            self.ds[var.short_name].attrs = var.to_dict()
    
    def _add_attrs(self):
        # Add global attributes
        self._add_global_attrs()
        # Add variable attributes
        self._add_variable_attrs()
        
    def _add_gridded_data(self):
        '''Add gridded data to the dataset, must be called after adding attrs'''
        ds_gridded = Gridder(self.ds).create_gridded_dataset()
        self.ds.update(ds_gridded)

    def process(self,return_ds=True):
        self._convert_df_to_ds()
        self._add_attrs()
        self._add_gridded_data()
        if return_ds:
            return self.ds
        
    def save(self,save_path=None):
        if self.ds is None:
            self.process()
        if save_path is None:
            save_path = self.netcdf_output_path
        self.ds.to_netcdf(save_path)
        return self.ds
        
    
# Test the processor class

memory_card_copy_path = Path('C:/Users/alecmkrueger/Documents/GERG/GERG_GitHub/GERG-Glider/Code/Packages/glider_ingest/src/tests/test_data/memory_card_copy')
working_dir = Path('C:/Users/alecmkrueger/Documents/GERG/GERG_GitHub/GERG-Glider/Code/Packages/glider_ingest/src/tests/test_data/working_dir')

processor = Processor(memory_card_copy_path=memory_card_copy_path,working_dir=working_dir,mission_num='46',mission_start_date='2024-06-28 02:58:28.873474121')

ds = processor.save()
ds