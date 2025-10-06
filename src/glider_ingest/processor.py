import pandas as pd
import xarray as xr
from pathlib import Path
from attrs import define, field
import datetime
import dbdreader
import shutil
import gsw
import random
import os
import logging

from .utils import find_nth, setup_logging
from .variable import Variable
from .gridder import Gridder
from .dataset_attrs import get_default_variables, get_global_attrs


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
    recopy_files: bool = field(default=False)  # If True, always recopy files even if they already exist
    include_gridded_data: bool = field(default=True)  # If True, include gridded data in the output dataset
    _log_level: str = field(default='INFO')  # Logging level for the application

    # Created attributes
    dbd: dbdreader.MultiDBD|None = field(default=None)
    _df: pd.DataFrame|None = field(default=None)
    ds: xr.Dataset|None = field(default=None)

    # Private backing fields
    _glider_id: str|None = field(default=None)
    _glider_name: str|None = field(default=None)
    _wmo_id: str|None = field(default=None)
    _mission_year: str|None = field(default=None)
    _mission_title: str|None = field(default=None)
    _mission_folder_name: str|None = field(default=None)
    _mission_folder_path: Path|None = field(default=None)
    _netcdf_filename: str|None = field(default=None)
    _netcdf_output_path: Path|None = field(default=None)
    _dbd_variables: list|None = field(default=None)
    _sci_dbd_variables: list|None = field(default=None)
    _eng_dbd_variables: list|None = field(default=None)
    _sci_df: pd.DataFrame|None = field(default=None)
    _eng_df: pd.DataFrame|None = field(default=None)
    _sci_ds: xr.Dataset|None = field(default=None)
    _eng_ds: xr.Dataset|None = field(default=None)


    @property
    def dbd_variables(self) -> list:
        return self.sci_dbd_vars + self.eng_dbd_vars

    @property
    def sci_dbd_vars(self) -> list:
        """Get the science DBD variables."""
        if self.dbd is None:
            self.dbd = self._read_dbd()
        return self.dbd.parameterNames['sci']

    @property
    def eng_dbd_vars(self) -> list:
        """Get the engineering DBD variables."""
        if self.dbd is None:
            self.dbd = self._read_dbd()
        return self.dbd.parameterNames['eng']

    @property
    def eng_vars(self) -> list:
        """Get engineering variables (non-calculated vars starting with 'm_')"""
        return [var.short_name for var in self.mission_vars
                if (not var.calculated) and (var.data_source_name.startswith('m_'))]  #type: ignore

    @property
    def sci_vars(self) -> list:
        """Get science variables (all non-engineering variables)"""
        return self.df.columns.drop(self.eng_vars).tolist()

    @property
    def glider_id(self) -> str|None:
        """Get the glider ID."""
        if self._glider_id is None:
            self._glider_id = self._get_glider_id()
        return self._glider_id

    @property
    def glider_name(self) -> str|None:
        """Get the glider name."""
        if self._glider_name is None:
            self._glider_name = self.glider_ids[self.glider_id]
        return self._glider_name

    @property
    def wmo_id(self) -> str|None:
        """Get the WMO ID."""
        if self._wmo_id is None:
            self._wmo_id = self.wmo_ids[self.glider_id]
        return self._wmo_id

    @property
    def mission_year(self) -> str:
        """Get the mission year."""
        if self._mission_year is None:
            self._mission_year = self._get_mission_year()
        return self._mission_year

    @property
    def mission_title(self) -> str:
        """Get the mission title."""
        if self._mission_title is None:
            self._mission_title = f'Mission {self.mission_num}'
        return self._mission_title

    @property
    def mission_folder_name(self) -> str:
        """Get the mission folder name."""
        if self._mission_folder_name is None:
            self._mission_folder_name = self.mission_title.replace(' ', '_')
        return self._mission_folder_name

    @property
    def mission_folder_path(self) -> Path:
        """Get the mission folder path."""
        if self._mission_folder_path is None:
            self._mission_folder_path = self.working_dir.joinpath(self.mission_folder_name)
        return self._mission_folder_path

    @property
    def netcdf_filename(self) -> str:
        """Get the NetCDF filename."""
        if self._netcdf_filename is None:
            self._netcdf_filename = f'M{self.mission_num}_{self.mission_year}_{self.glider_id}.nc'
        return self._netcdf_filename

    @property
    def netcdf_output_path(self) -> Path:
        """Get the NetCDF path."""
        if self._netcdf_output_path is None:
            self._netcdf_output_path = self.mission_folder_path.joinpath(f'{self.netcdf_filename}')
        return self._netcdf_output_path

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            self._df = self._convert_dbd_to_dataframe()
        return self._df

    @property
    def sci_df(self) -> pd.DataFrame:
        return self.df[self.sci_vars]

    @property
    def eng_df(self) -> pd.DataFrame:
        eng_df = self.df[self.eng_vars].copy()
        eng_df.index.name = 'm_time'
        return eng_df

    @property
    def sci_ds(self) -> xr.Dataset:
        return xr.Dataset.from_dataframe(self.sci_df)

    @property
    def eng_ds(self) -> xr.Dataset:
        return xr.Dataset.from_dataframe(self.eng_df)

    @property
    def log_level(self) -> str:
        """Get the current logging level."""
        return self._log_level

    @log_level.setter
    def log_level(self, level: str):
        """Set the logging level and update the logger configuration."""
        self._log_level = level.upper()
        setup_logging(level=self._log_level)

    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance for this processor."""
        return logging.getLogger('glider_ingest')

    def __attrs_post_init__(self):
        """
        Post init method to add default variables to the mission_vars list
        """
        setup_logging(level=self._log_level)
        self.logger.info("Initializing Processor for mission %s", self.mission_num)
        self.logger.debug("Memory card path: %s", self.memory_card_copy_path)
        self.logger.debug("Working directory: %s", self.working_dir)

        self.add_mission_vars(get_default_variables())
        self.logger.info("Added %d default variables", len(get_default_variables()))

    def _check_mission_var_duplicates(self):
        """
        Check for duplicate variables in the mission_vars list
        """
        # Get the variable data_source_names
        var_names = self._get_mission_variable_short_names()
        if len(set(var_names)) != len(var_names):
            print('Duplicate variables in mission_vars list')

    def add_mission_vars(self, mission_vars: list[Variable]|list[str]|Variable|str):
        """
        Add variables to the mission_vars list.

        Args:
            mission_vars: Can be any of:
            - Single Variable object
            - Single string
            - List of Variable objects
            - List of strings
            - Mixed list of Variables and strings
        """
        # Convert to list if single item
        if isinstance(mission_vars, Variable):
            mission_vars = [mission_vars]
        elif isinstance(mission_vars, str):
            mission_vars = [mission_vars]

        self.logger.debug("Adding %d variables to mission_vars", len(mission_vars))

        # Process each variable
        processed_vars = []
        for var in mission_vars:
            if isinstance(var, str):
                processed_vars.append(Variable(data_source_name=var))
                self.logger.debug("Added string variable: %s", var)
            elif isinstance(var, Variable):
                processed_vars.append(var)
                self.logger.debug("Added Variable object: %s", var.data_source_name)

        self.mission_vars.extend(processed_vars)
        self.logger.info("Total mission variables: %d", len(self.mission_vars))
        self._check_mission_var_duplicates()

    def remove_mission_vars(self, vars_to_remove: list[str]|str):
        """
        Remove variables from mission_vars list by data source name.

        Args:
            vars_to_remove: Can be a single string or list of strings representing
                        data_source_names to remove
        """
        # Convert single string to list
        if isinstance(vars_to_remove, str):
            vars_to_remove = [vars_to_remove]

        self.logger.info("Removing %d variables: %s", len(vars_to_remove), vars_to_remove)
        initial_count = len(self.mission_vars)

        # Filter out the variables to remove
        self.mission_vars = [var for var in self.mission_vars
                            if var.data_source_name not in vars_to_remove]

        removed_count = initial_count - len(self.mission_vars)
        self.logger.info("Successfully removed %d variables. Remaining: %d", removed_count, len(self.mission_vars))

    def _copy_files(self):
        """
        Copy only LOGS and STATE/CACHE folders from memory card copy to working directory
        """
        self.logger.info("Starting file copy operation")
        original_loc = self.memory_card_copy_path
        new_loc = self.mission_folder_path

        self.logger.debug("Source: %s", original_loc)
        self.logger.debug("Destination: %s", new_loc)

        # Define patterns to include
        include_patterns = ['**/LOGS', '**/logs', '**/STATE/CACHE', '**/state/cache']
        copied_count = 0
        skipped_count = 0

        for pattern in include_patterns:
            self.logger.debug("Processing pattern: %s", pattern)
            for source_path in original_loc.glob(pattern):
                # Create relative path to maintain directory structure
                relative_path = source_path.relative_to(original_loc)
                destination_path = new_loc / relative_path

                # Skip copying if files already exist and recopy_files is False
                if destination_path.exists() and not self.recopy_files:
                    self.logger.debug("Skipping existing directory: %s", destination_path)
                    skipped_count += 1
                    continue

                # Create parent directories if they don't exist
                destination_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy directory
                if source_path.is_dir():
                    self.logger.info('Copying %s to %s', source_path, destination_path)
                    shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
                    copied_count += 1

        self.logger.info("File copy complete. Copied: %d, Skipped: %d", copied_count, skipped_count)


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
        directory_path = self.memory_card_copy_path
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
        # Look for cache files in Flight_card/STATE/CACHE
        cache_source = self.memory_card_copy_path / 'Flight_card' / 'STATE' / 'CACHE'
        cache_dest = self.mission_folder_path / 'Flight_card' / 'STATE' / 'CACHE'

        if not cache_source.exists():
            return

        if not cache_dest.exists():
            cache_dest.mkdir(parents=True, exist_ok=True)

        for cache_file in cache_source.iterdir():
            if cache_file.is_file():
                dest_file = cache_dest / cache_file.name
                # check if cache file already exists
                if dest_file.exists() and not self.recopy_files:
                    continue
                # copy cache file
                print(f'copying {cache_file} to {cache_dest}')
                shutil.copy2(cache_file, dest_file)

    def _get_dbd_files(self,as_string=False):
        """
        Get the dbd files from the memory card copy
        """
        directory_path = self.mission_folder_path
        extensions = ['.dbd','.DBD','.ebd','.EBD']
        dbd_files = self._get_files_by_extension(directory_path=directory_path,extensions=extensions,as_string=as_string)
        return dbd_files

    def _read_dbd(self) -> dbdreader.MultiDBD:
        """
        Read the files from the memory card copy
        """
        self.logger.info("Reading DBD files")
        self._copy_files()
        self._copy_cache_files()

        filenames = self._get_dbd_files(as_string=True)
        self.logger.info("Found %d DBD files", len(filenames))
        self.logger.debug("DBD files: %s%s", [Path(f).name for f in filenames[:5]], '...' if len(filenames) > 5 else '')

        cacheDir = self._get_cache_files_path()
        self.logger.debug("Cache directory: %s", cacheDir)

        dbd = dbdreader.MultiDBD(filenames=filenames,cacheDir=cacheDir)
        self.logger.info("Successfully initialized MultiDBD reader")
        return dbd

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

    def _check_default_variables(self,variables_to_get:list):
        """
        Check that the default variables are in the dbd variables and remove missing ones from both the list and mission_vars
        """
        self.logger.debug("Checking variable availability in DBD files")
        dbd_vars = self.dbd_variables
        self.logger.info(f"DBD contains {len(dbd_vars)} total variables")

        missing_vars = [var for var in variables_to_get if var not in dbd_vars]
        if missing_vars:
            self.logger.warning(f'Missing variables in DBD files: {missing_vars}')
            self.logger.info('Removing missing variables from processing list')
            variables_to_get = [var for var in variables_to_get if var not in missing_vars]
            # Also remove missing variables from mission_vars to maintain consistency
            self.mission_vars = [var for var in self.mission_vars
                               if var.data_source_name not in missing_vars]
        else:
            self.logger.info("All requested variables found in DBD files")

        self.logger.info("Final variable count for processing: %d", len(variables_to_get))
        return variables_to_get

    def _get_sci_files(self):
        """
        Get the sci files from the memory card copy
        """
        directory_path = self.memory_card_copy_path
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
        if full_filename is None:
            self.logger.error("Could not extract full filename from DBD files")
            return "unknown"
        mission_year = full_filename[full_filename.find('-') + 1: find_nth(full_filename, '-', 2)].strip()
        return mission_year

    def _get_glider_id(self) -> str|None:
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
        if full_filename is None:
            self.logger.error("Could not extract full filename from DBD files")
            return None
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
        self.logger.info("Extracting data from DBD files")
        self.dbd = self._read_dbd()

        variables_to_get = self._get_mission_variable_data_source_names(filter_out_none=True)
        self.logger.info("Requesting %d variables", len(variables_to_get))

        variables_to_get = self._check_default_variables(variables_to_get)

        self.logger.info("Synchronizing data extraction...")
        data = self.dbd.get_sync(*variables_to_get)
        self.logger.info("Successfully extracted data with variables of: %s", variables_to_get)

        self.dbd.close()
        return data, variables_to_get

    def _format_time(self,df:pd.DataFrame):
        self.logger.debug("Formatting time data")
        initial_rows = len(df)

        # Convert time to datetime format and filter valid dates
        df['time'] = pd.to_datetime(df['time'],unit='s', errors='coerce')
        df = df.dropna(how='all')
        after_dropna = len(df)

        valid_dates_mask = (df['time'] >= self.mission_start_date) & \
                           (df['time'] <= self.mission_end_date)
        df = df.loc[valid_dates_mask]
        final_rows = len(df)

        self.logger.info("Time filtering: %d -> %d -> %d rows", initial_rows, after_dropna, final_rows)
        if final_rows > 0:
            self.logger.info("Time range: %s to %s", df['time'].min(), df['time'].max())
        else:
            self.logger.warning("No data remaining after time filtering")

        return df

    def _calculate_vars(self,df):
        self.logger.info("Performing variable calculations and conversions")

        # Perform variable conversions and calculations
        if 'm_pressure' in df.columns:
            df['m_pressure'] *= 10  # Convert pressure from db to dbar
            self.logger.debug("Converted m_pressure from db to dbar")

        if 'sci_water_pressure' in df.columns:
            df['sci_water_pressure'] *= 10  # Convert pressure from db to dbar
            self.logger.debug("Converted sci_water_pressure from db to dbar")

        if 'sci_water_cond' in df.columns:
            df['sci_water_cond'] *= 1000  # Convert conductivity from mS/cm to S/m
            self.logger.debug("Converted sci_water_cond from mS/cm to S/m")

        vars_for_salinity_and_density = {'sci_water_cond', 'sci_water_temp', 'sci_water_pressure'}
        if vars_for_salinity_and_density.issubset(df.columns):
            self.logger.info("Calculating salinity and density from CTD data")
            df['salinity'] = gsw.SP_from_C(df['sci_water_cond'] * 10, df['sci_water_temp'], df['sci_water_pressure'])
            CT = gsw.CT_from_t(df['salinity'], df['sci_water_temp'], df['sci_water_pressure'])
            df['density'] = gsw.rho_t_exact(df['salinity'], CT, df['sci_water_pressure'])
            self.logger.debug("Calculated salinity range: %.2f - %.2f", df['salinity'].min(), df['salinity'].max())
            self.logger.debug("Calculated density range: %.2f - %.2f", df['density'].min(), df['density'].max())
        else:
            self.logger.warning("Cannot calculate salinity/density - missing required CTD variables")

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
        data, variables_retrieved = self._get_dbd_data()
        df = pd.DataFrame(data).T
        new_column_names = ['time']
        new_column_names.extend(variables_retrieved)
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
        return df

    def _generate_ds(self):
        """
        Generate a xarray dataset from the dataframe
        """
        self.logger.info("Generating xarray dataset")

        # self.ds = xr.Dataset.from_dataframe(self.df)
        self.logger.debug("Merging science and engineering datasets")
        self.ds = xr.merge([self.sci_ds, self.eng_ds])
        self.logger.info("Created dataset with %d variables and %d coordinates", len(self.ds.data_vars), len(self.ds.coords))

        self.logger.debug("Adding global attributes")
        self._add_global_attrs()

        self.logger.debug("Adding variable attributes")
        self._add_variable_attrs()

        self.logger.info("Dataset generation complete")
        return self.ds

    def _get_longitude(self):
        if self.ds is None:
            self.logger.error("Dataset not generated yet, run process() first")
            raise ValueError("Dataset not generated yet, run process() first")
        return self.ds.longitude.values

    def _get_latitude(self):
        if self.ds is None:
            self.logger.error("Dataset not generated yet, run process() first")
            raise ValueError("Dataset not generated yet, run process() first")
        return self.ds.latitude.values

    def _get_depth(self):
        if self.ds is None:
            self.logger.error("Dataset not generated yet, run process() first")
            raise ValueError("Dataset not generated yet, run process() first")
        return self.ds.depth.values

    def _get_time(self):
        if self.ds is None:
            self.logger.error("Dataset not generated yet, run process() first")
            raise ValueError("Dataset not generated yet, run process() first")
        return self.ds.time.values

    def _add_global_attrs(self):
        if self.wmo_id is None:
            self.logger.error("WMO ID is None, cannot add global attributes")
            raise ValueError("WMO ID is None, cannot add global attributes")
        global_attrs = get_global_attrs(wmo_id = self.wmo_id,mission_title=self.mission_title,
                                        longitude=self._get_longitude(),latitude=self._get_latitude(),
                                        depth=self._get_depth(),time=self._get_time())

        if self.ds is None:
            self.logger.error("Dataset not generated yet, run process() first")
            raise ValueError("Dataset not generated yet, run process() first")

        self.ds.attrs = global_attrs

    def _add_variable_attrs(self):
        if self.ds is None:
            self.logger.error("Dataset not generated yet, run process() first")
            raise ValueError("Dataset not generated yet, run process() first")
        for var in self.mission_vars:
            self.ds[var.short_name].attrs = var.to_dict()

    def _add_gridded_data(self):
        '''Add gridded data to the dataset, must be called after adding attrs'''
        if self.ds is None:
            self.logger.error("Dataset not generated yet, run process() first")
            raise ValueError("Dataset not generated yet, run process() first")
        ds_gridded = Gridder(self.ds).create_gridded_dataset()
        self.ds.update(ds_gridded)

    def process(self,return_ds=True):
        self.logger.info("=== Starting data processing ===")
        start_time = pd.Timestamp.now()

        self._generate_ds()

        if self.include_gridded_data:
            self.logger.info("Adding gridded data to dataset")
            self._add_gridded_data()
        else:
            self.logger.info("Skipping gridded data (disabled)")

        processing_time = pd.Timestamp.now() - start_time
        self.logger.info("=== Processing complete in %.2f seconds ===", processing_time.total_seconds())

        if return_ds:
            return self.ds

    def save(self,save_path=None):
        if self.ds is None:
            self.logger.info("Dataset not generated yet, running process()")
            self.process()

        if save_path is None:
            save_path = self.netcdf_output_path

        self.logger.info("Saving dataset to: %s", save_path)

        # Create directory if it doesn't exist
        save_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = pd.Timestamp.now()
        if self.ds is None:
            self.logger.error("Dataset not generated yet, run process() first")
            raise ValueError("Dataset not generated yet, run process() first")
        self.ds.to_netcdf(save_path)
        save_time = pd.Timestamp.now() - start_time

        file_size_mb = save_path.stat().st_size / (1024 * 1024)
        self.logger.info("Dataset saved successfully (%.2f MB) in %.2f seconds", file_size_mb, save_time.total_seconds())

        return self.ds
