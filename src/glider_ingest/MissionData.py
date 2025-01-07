import pandas as pd
import xarray as xr
from pathlib import Path
from attrs import define, field
import datetime

from glider_ingest.utils import find_nth, invert_dict


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
        """
        Retrieves files with a specific extension from the specified directory.

        Args:
            files_loc (Path): The directory where the files are located.
            extension (str): The file extension to search for.

        Returns:
            list: A list of file paths matching the extension.

        Raises:
            ValueError: If no files are found or the directory does not exist.
        """
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
