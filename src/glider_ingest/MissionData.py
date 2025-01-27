import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from attrs import define, field
import datetime
import uuid

from glider_ingest.utils import find_nth, get_polygon_coords,print_time
from glider_ingest.variable import Variable
from glider_ingest.gridder import Gridder


@define
class MissionData:
    """
    A class representing glider mission data and metadata.

    This class provides methods for managing and processing data
    related to a specific glider mission, including setup, 
    file location retrieval, metadata extraction, and NetCDF file generation.

    Attributes:
        memory_card_copy_loc (Path): Location of the copied memory card.
        working_dir (Path): Working directory for mission data processing.
        mission_num (str): Mission number identifier.
        glider_id (str): Identifier of the glider.
        nc_filename (str): NetCDF filename.
        output_nc_path (Path): Path for the output NetCDF file.
        mission_start_date (str | None): Start date of the mission.
        mission_end_date (str | None): End date of the mission.
        mission_year (str): Year of the mission.
        mission_title (str): Title of the mission.
        glider_name (str): Name of the glider.
        glider_ids (dict): Mapping of glider IDs to names.
        wmo_ids (dict): Mapping of glider IDs to WMO IDs.
        wmo_id (str): WMO ID for the glider.
        mission_vars (dict): Dictonary of mission variables.

    Post-Initialization Attributes:
        fli_files_loc (Path): Path to flight logs.
        fli_cache_loc (Path): Path to flight cache.
        sci_files_loc (Path): Path to science logs.
        sci_cache_loc (Path): Path to science cache.
        df_fli (pd.DataFrame): DataFrame for flight data.
        ds_fli (xr.Dataset): Dataset for flight data.
        df_sci (pd.DataFrame): DataFrame for science data.
        ds_sci (xr.Dataset): Dataset for science data.
        ds_mission (xr.Dataset): Combined dataset for mission data.
    """

    # Required Variables
    memory_card_copy_loc: Path
    working_dir: Path
    mission_num: str

    # Optional Variables
    glider_id: str = field(default=None)
    nc_filename: str = field(default=None)
    output_nc_path: Path = field(default=None)
    mission_start_date: str | None = field(default=None)
    mission_end_date: str | None = field(default=None)
    mission_year: str = field(default=None)
    mission_title: str = field(default=None)
    glider_name: str = field(default=None)
    glider_ids: dict = field(default={'199': 'Dora', '307': 'Reveille', '308': 'Howdy', '540': 'Stommel', '541': 'Sverdrup', '1148': 'unit_1148'})
    wmo_ids: dict = field(default={'199': 'unknown', '307': '4801938', '308': '4801915', '540': '4801916', '541': '4801924', '1148': '4801915'})
    wmo_id: str = field(default=None)
    mission_vars: dict|None = field(default={})  # Dictonary of mission variables with keys:Variable.data_source_name and values:Variable

    # Post init variables
    fli_files_loc: Path = field(init=False)
    fli_cache_loc: Path = field(init=False)
    sci_files_loc: Path = field(init=False)
    sci_cache_loc: Path = field(init=False)

    # Data Ingest Variables
    df_fli: pd.DataFrame = field(init=False)
    ds_fli: xr.Dataset = field(init=False)

    df_sci: pd.DataFrame = field(init=False)
    ds_sci: xr.Dataset = field(init=False)

    ds_mission: xr.Dataset = field(init=False)

    def __attrs_post_init__(self):
        """
        Post-initialization method to set up file locations for the mission data.

        This method is called automatically after the object is initialized to define paths for
        flight card logs, science card logs, and their respective caches.
        """
        self.get_file_locs()
        self.init_base_variables()
    
    def init_base_variables(self):
        """
        Initializes the base variables.
        """
        from glider_ingest.variable import Variable
        import glider_ingest.dataset_attrs as attrs

        # Get all Variable objects dynamically
        variables_list = [getattr(attrs, attr) for attr in dir(attrs) 
                        if isinstance(getattr(attrs, attr), Variable)]
        
        self.add_variables(variables_list)

    def setup(self):
        """
        Initializes the mission data by setting up necessary attributes like mission date range,
        year, glider information, WMO ID, mission title, and NetCDF filename.

        This method should be called after initialization to configure the mission object fully.
        """
        self.get_mission_date_range()
        self.get_mission_year_and_glider()
        self.get_wmo_id()
        self.get_mission_title()
        self.get_nc_filename()
        self.get_output_nc_path()

    def get_file_locs(self):
        """
        Defines and sets the file locations for flight card and science card data, including caches.

        This method checks for case-insensitivity in file path locations to ensure proper retrieval
        of files, whether the case is uppercase or lowercase.
        """
        def set_path_with_case(base_path: Path, *parts: str) -> Path:
            """
            Helper function to set the path while handling case-insensitivity.

            Args:
                base_path (Path): The base path to start with.
                *parts (str): The path components to join with the base path.

            Returns:
                Path: The resulting path with the specified components.
            """
            path = base_path.joinpath(*parts)
            if path.exists():
                return path
            return base_path.joinpath(*parts[:-1], parts[-1].upper())

        self.fli_files_loc = set_path_with_case(self.memory_card_copy_loc, 'Flight_card', 'logs')
        self.fli_cache_loc = set_path_with_case(self.memory_card_copy_loc, 'Flight_card', 'state', 'cache')
        self.sci_files_loc = set_path_with_case(self.memory_card_copy_loc, 'Science_card', 'logs')
        self.sci_cache_loc = set_path_with_case(self.memory_card_copy_loc, 'Science_card', 'state', 'cache')

    def get_mission_date_range(self):
        """
        Sets the mission start and end dates if not provided. Default start date is '2010-01-01' and
        the end date is set to one year after the current date.

        This method ensures that if the mission dates are not provided, reasonable defaults are applied.
        """
        if self.mission_end_date is None:
            self.mission_end_date = str(datetime.datetime.today().date() + datetime.timedelta(days=365))
        if self.mission_start_date is None:
            self.mission_start_date = '2010-01-01'

    def get_mission_year_and_glider(self):
        """
        Extracts the mission year and glider details from a sample file.

        This method identifies the year of the mission from the file name and validates the glider's name
        or ID against a predefined list of possible values.
        """
        file = self._get_sample_file()
        name = self._extract_full_filename(file)
        self._parse_mission_year(name)
        self._parse_and_validate_glider_name(name)
        
    def add_variables(self,variables:list[Variable],debug=False):
        """Adds variables to the mission data.

        Args:
            variables (list): list of Variable objects to add to the mission data.
        """
        # Validate list of variables are of type Variable
        if all(isinstance(var, str) for var in variables):
            # Convert strings to Variable objects for basic implementation
            variables = [Variable(data_source_name=var) for var in variables]
        if not all(isinstance(var, Variable) for var in variables):
            raise TypeError("All elements in the list must be of type Variable or string.")
        # Add variables to mission_vars dictionary
        if debug:
            print(f"Adding variables: {[var.data_source_name for var in variables]}")
        variables_dict = {var.data_source_name: var for var in variables}
        self.mission_vars.update(variables_dict)
        

    def _get_sample_file(self):
        """
        Retrieves a sample file from the science card files directory.

        Returns:
            str: A path to a sample file from the science card directory.
        """
        files = self.get_files(files_loc=self.sci_files_loc, extension='ebd')
        return files[10]

    def _extract_full_filename(self, file):
        """
        Extracts the full filename from a given file based on specific content.

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

    def _parse_mission_year(self, name):
        """
        Parses the mission year from the full filename.

        Args:
            name (str): The full filename string.
        """
        self.mission_year = name[name.find('-') + 1: find_nth(name, '-', 2)].strip()

    def _parse_and_validate_glider_name(self, name):
        """
        Parses and validates the glider name from the mission file name.

        Args:
            name (str): The full filename string.

        Raises:
            ValueError: If the glider name is not found or is invalid.
        """
        glider_name = name.split('-')[0].replace('unit_', '').strip()
        
        inverted_glider_ids = {v: k for k, v in self.glider_ids.items()}
        
        if glider_name in self.glider_ids:
            self.glider_name = self.glider_ids[glider_name]
            self.glider_id = glider_name
            return
            
        if glider_name in inverted_glider_ids:
            self.glider_name = glider_name
            self.glider_id = inverted_glider_ids[glider_name]
            return
            
        valid_options = list(self.glider_ids.keys()) + list(self.glider_ids.values())
        raise ValueError(f'Invalid glider identifier: {glider_name}. Must be one of: {valid_options}')

    def get_mission_title(self):
        """
        Sets the mission title if not provided. Defaults to 'Mission {mission_num}'.

        This method ensures that if the mission title is not specified, a default title is generated
        using the mission number.
        """
        if self.mission_title is None:
            self.mission_title = f'Mission {self.mission_num}'

    def get_nc_filename(self):
        """
        Generates the NetCDF filename based on the mission number, year, and glider ID.

        This method ensures that a valid filename is created if not provided.
        """
        if self.nc_filename is None:
            self.nc_filename = f'M{self.mission_num}_{self.mission_year}_{self.glider_id}.nc'

    def get_output_nc_path(self):
        """
        Determines the output NetCDF file path based on the working directory and mission title.

        This method ensures that the directory exists and the file path is set up correctly.
        """
        if self.output_nc_path is None:
            output_nc_loc = self.working_dir.joinpath(self.mission_title)
            output_nc_loc.mkdir(exist_ok=True, parents=True)
            self.output_nc_path = output_nc_loc.joinpath(self.nc_filename)
        if isinstance(self.output_nc_path, str):
            self.output_nc_path = Path(self.output_nc_path)
        if isinstance(self.output_nc_path, Path):
            if not self.output_nc_path.is_file():
                self.output_nc_path.joinpath(self.nc_filename)

    def get_wmo_id(self):
        """
        Retrieves the WMO identifier for the glider based on its ID.

        If the WMO ID is not provided, it looks up the value from the `wmo_ids` dictionary.
        """
        if self.wmo_id is None:
            self.wmo_id = self.wmo_ids[self.glider_id]

    def get_files(self, files_loc: Path, extension: str):
        if files_loc.exists():
            try:
                files = list(files_loc.rglob(f'*.{extension.lower()}'))
                files = [str(file) for file in files]
                if len(files) == 0:
                    raise ValueError(f'No Files found at {files_loc.resolve()}')
            except ValueError:
                files = list(files_loc.rglob(f'*.{extension.upper()}'))
                files = [str(file) for file in files]
                if len(files) == 0:
                    raise ValueError(f'No Files found at {files_loc.resolve()}')
            return files
        else:
            raise ValueError(f'Path not found: {files_loc.resolve()}')
        
    def rename_mission_variables(self):
        """
        Renames mission-specific variables in the NetCDF dataset.
        """
        for key,variable in self.mission_vars.items():
            if variable.data_source_name in self.ds_mission.data_vars.keys():
                self.ds_mission = self.ds_mission.rename({variable.data_source_name: variable.short_name})
            else:
                print(f'{variable.data_source_name}:{variable.short_name} not in dataset')
      
    def add_gridded_data(self) -> None:
        """
        Add gridded data to the mission dataset using the Gridder class.

        Notes
        -----
        This method creates a `Gridder` object to compute the gridded dataset,
        updates the mission dataset with the gridded data, and prints timing information.
        """
        
        print_time('Adding Gridded Data')
        
        # Create Gridder object with the mission dataset
        gridder = Gridder(ds_mission=self.ds_mission)
        
        # Generate the gridded dataset 
        gridder.create_gridded_dataset()
        
        # Update the mission dataset with the gridded dataset
        self.ds_mission.update(gridder.ds_gridded)
        
        print_time('Finished Adding Gridded Data')

        
    def add_global_attrs(self):
        self.ds_mission.attrs = {'Conventions': 'CF-1.6, COARDS, ACDD-1.3',
        'acknowledgment': ' ',
        'cdm_data_type': 'Profile',
        'comment': 'time is the ctd_time from sci_m_present_time, m_time is the gps_time from m_present_time, g_time and g_pres are the grided time and pressure',
        'contributor_name': 'Steven F. DiMarco',
        'contributor_role': ' ',
        'creator_email': 'sakib@tamu.edu, gexiao@tamu.edu',
        'creator_institution': 'Texas A&M University, Geochemical and Environmental Research Group',
        'creator_name': 'Sakib Mahmud, Xiao Ge',
        'creator_type': 'persons',
        'creator_url': 'https://gerg.tamu.edu/',
        'date_created': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
        'date_issued': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
        'date_metadata_modified': '2023-09-15',
        'date_modified': pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
        'deployment': ' ',
        'featureType': 'profile',
        'geospatial_bounds_crs': 'EPSG:4326',
        'geospatial_bounds_vertical_crs': 'EPSG:5831',
        'geospatial_lat_resolution': "{:.4e}".format(abs(np.nanmean(np.diff(self.ds_mission.latitude))))+ ' degree',
        'geospatial_lat_units': 'degree_north',
        'geospatial_lon_resolution': "{:.4e}".format(abs(np.nanmean(np.diff(self.ds_mission.longitude))))+ ' degree',
        'geospatial_lon_units': 'degree_east',
        'geospatial_vertical_positive': 'down',
        'geospatial_vertical_resolution': ' ',
        'geospatial_vertical_units': 'EPSG:5831',
        'infoUrl': 'https://gerg.tamu.edu/',
        'institution': 'Texas A&M University, Geochemical and Environmental Research Group',
        'instrument': 'In Situ/Laboratory Instruments > Profilers/Sounders > CTD',
        'instrument_vocabulary': 'NASA/GCMD Instrument Keywords Version 8.5',
        'ioos_regional_association': 'GCOOS-RA',
        'keywords': 'Oceans > Ocean Pressure > Water Pressure, Oceans > Ocean Temperature > Water Temperature, Oceans > Salinity/Density > Conductivity, Oceans > Salinity/Density > Density, Oceans > Salinity/Density > Salinity',
        'keywords_vocabulary': 'NASA/GCMD Earth Sciences Keywords Version 8.5',
        'license': 'This data may be redistributed and used without restriction.  Data provided as is with no expressed or implied assurance of quality assurance or quality control',
        'metadata_link': ' ',
        'naming_authority': 'org.gcoos.gandalf',
        'ncei_template_version': 'NCEI_NetCDF_Trajectory_Template_v2.0',
        'platform': 'In Situ Ocean-based Platforms > AUVS > Autonomous Underwater Vehicles',
        'platform_type': 'Slocum Glider',
        'platform_vocabulary': 'NASA/GCMD Platforms Keywords Version 8.5',
        'processing_level': 'Level 0',
        'product_version': '0.0',
        'program': ' ',
        'project': ' ',
        'publisher_email': 'sdimarco@tamu.edu',
        'publisher_institution': 'Texas A&M University, Geochemical and Environmental Research Group',
        'publisher_name': 'Steven F. DiMarco',
        'publisher_url': 'https://gerg.tamu.edu/',
        'references': ' ',
        'sea_name': 'Gulf of Mexico',
        'standard_name_vocabulary': 'CF Standard Name Table v27',
        'summary': 'Merged dataset for GERG future usage.',
        'time_coverage_resolution': ' ',
        'wmo_id': self.wmo_id,
        'uuid': str(uuid.uuid4()),
        'history': 'dbd and ebd files transferred from dbd2asc on 2023-09-15, merged into single netCDF file on '+pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
        'title': self.mission_title,
        'source': 'Observational Slocum glider data from source ebd and dbd files',
        'geospatial_lat_min': str(np.nanmin(self.ds_mission.latitude[np.where(self.ds_mission.latitude.values<29.5)].values)),
        'geospatial_lat_max': str(np.nanmax(self.ds_mission.latitude[np.where(self.ds_mission.latitude.values<29.5)].values)),
        'geospatial_lon_min': str(np.nanmin(self.ds_mission.longitude.values)),
        'geospatial_lon_max': str(np.nanmax(self.ds_mission.longitude.values)),
        'geospatial_bounds': get_polygon_coords(self.ds_mission),
        'geospatial_vertical_min': str(np.nanmin(self.ds_mission.depth[np.where(self.ds_mission.depth>0)].values)),
        'geospatial_vertical_max': str(np.nanmax(self.ds_mission.depth.values)),
        'time_coverage_start': str(self.ds_mission.time[-1].values)[:19],
        'time_coverage_end': str(self.ds_mission.m_time[-1].values)[:19],
        'time_coverage_duration': 'PT'+str((self.ds_mission.m_time[-1].values - self.ds_mission.time[-1].values) / np.timedelta64(1, 's'))+'S'}
    

    def add_attrs(self):
        """Adds flight, science, and mission attributes to the dataset."""
        # Get the mission dataset data_vars
        variables = list(self.ds_mission.data_vars)
        for var in self.mission_vars.values():
            if var.short_name in variables:
                self.ds_mission[var.short_name].attrs = var.to_dict()
        
        # Add platform attributes                
        platform = Variable(
            ancillary_variables='',
            comment='',
            id=self.glider_id,
            instruments='instrument_ctd',
            long_name='Slocum Glider '+ self.glider_id,
            type='platform',
            wmo_id=self.wmo_id,
        )
        self.ds_sci['platform'].attrs = platform.to_dict()
        self.add_global_attrs()
        
