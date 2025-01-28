import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from attrs import define, field
import datetime
import uuid
import dbdreader
import shutil
import gsw
import time
import random

from glider_ingest.utils import get_polygon_coords,print_time
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
    # global_attrs: dict = field(default=None)  # found in get_global_attrs
    
    # Optional attributes
    mission_start_date: datetime.datetime = field(default=pd.to_datetime('2010-01-01'))  # Used to slice the data during processing
    mission_end_date: datetime.datetime = field(default=pd.to_datetime(datetime.datetime.today()+datetime.timedelta(days=365)))  # Used to slice the data during processing
    
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
            raise ValueError('Duplicate variables in mission_vars list')
        
    def add_mission_vars(self, mission_vars: list[Variable]):
        """
        Add a variable to the mission_vars list
        """
        self.mission_vars.extend(mission_vars)
        self._check_mission_var_duplicates()
        
    def _get_mission_title(self):
        """
        Get the mission title from the mission_num
        """
        return f'Mission {self.mission_num}'
    
    def _get_mission_folder_name(self):
        """
        Get the mission folder name from the mission_title
        """
        return self._get_mission_title().replace(' ', '_')
    
    def _get_mission_folder_path(self):
        """
        Get the mission copy location from the mission_num
        """
        return self.working_dir.joinpath(self._get_mission_folder_name())
    
    def _copy_files(self):
        """
        Copy the memory card copy files to the working directory
        """
        original_loc = self.memory_card_copy_path
        new_loc = self._get_mission_folder_path()
        shutil.copytree(original_loc, new_loc, dirs_exist_ok=True)

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
        directory_path = self._get_mission_folder_path()
        cac_files = self._get_files_by_extension(directory_path=directory_path,extensions=extensions,as_string=as_string)
        return cac_files

    def _get_cache_files_path(self):
        """
        Get the cache file path from the memory card copy
        """
        return self._get_mission_folder_path().joinpath('cache')

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
        directory_path = self._get_mission_folder_path()
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
            raise ValueError(f'The following variables are missing from the dbd files: {missing_vars}')
        
    def _get_sci_files(self):
        """
        Get the sci files from the memory card copy
        """
        directory_path = self._get_mission_folder_path()
        extensions = ['.dbd','.DBD']
        sci_files = self._get_files_by_extension(directory_path=directory_path,extensions=extensions,as_string=True)
        return sci_files
        
    def _get_random_sci_file(self):
        """
        Get a random sci file from the mission folder
        """
        sci_files = self._get_sci_files()
        return random.choice(sci_files)
        
    def _get_full_filename_from_file(self,file):
        """
        Get the full filename from the file
        Args:
            file (str): Path to the file to read.

        Returns:
            str: The extracted full filename, or None if not found.
        """
        with open(file, errors="ignore") as fp:
            for line in fp:
                if 'full_filename' in line.strip():
                    return line.replace('full_filename:', '').strip()
        return None
        
    def _get_glider_id(self):
        """
        Get the glider id from the mission_vars list
        """
        file = self._get_random_sci_file()
        fulll_filename = self._get_full_filename_from_file(self._get_mission_folder_path().joinpath('mission.txt'))
        raise NotImplementedError
        
    def _get_wmo_id(self):
        """
        Get the wmo id from the mission_vars list
        """
        raise NotImplementedError
    
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
    
    def _get_dbd_dataframe(self):
        """
        Get the dbd data as a dataframe
        """
        data = self._get_dbd_data()
        df = pd.DataFrame(data).T
        new_column_names = ['time']
        new_column_names.extend(self._get_mission_variable_data_source_names(filter_out_none=True))
        if len(df.columns) != len(new_column_names):
            raise ValueError(f'The number of columns in the dataframe does not match the number of mission variables, {df.columns} vs {new_column_names}')
        # Add names to the dataframe columns
        df.columns = new_column_names
        # Format time
        df = self._format_time(df)
        # Calculate variables
        df = self._calculate_vars(df)
        # Set time as index
        df = df.set_index('time')
        return df
    
    def _convert_to_ds(self):
        df = self._get_dbd_dataframe()
        ds = xr.Dataset.from_dataframe(df)
        return ds
    
    def _add_global_attrs(self):
        from glider_ingest.dataset_attrs import get_global_attrs
        global_attrs = get_global_attrs(wmo_id = self._get_wmo_id(),
                                        mission_title=self._get_mission_title(),
                                        longitude=self._get_longitude(),
                                        latitude=self._get_latitude(),depth=self._get_depth(),
                                        time=self._get_time())
                                        
    
    def _add_attrs(self):
        ''''''
        
    
# Test the processor class

memory_card_copy_path = Path('C:/Users/alecmkrueger/Documents/GERG/GERG_GitHub/GERG-Glider/Code/Packages/glider_ingest/src/tests/test_data/memory_card_copy')
working_dir = Path('C:/Users/alecmkrueger/Documents/GERG/GERG_GitHub/GERG-Glider/Code/Packages/glider_ingest/src/tests/test_data/working_dir')

processor = Processor(memory_card_copy_path=memory_card_copy_path,working_dir=working_dir,mission_num='46',mission_start_date='2024-06-28 02:58:28.873474121')

ds = processor._convert_to_ds()
ds
