import pandas as pd
import xarray as xr
from pathlib import Path
from attrs import define,field,asdict
import datetime
import os
from pprint import pformat


from glider_ingest.utils import find_nth,invert_dict

@define
class MissionData:
    # Required Variables
    memory_card_copy_loc:Path
    working_dir:Path
    mission_num:str

    # Optional Variables
    glider_id:str = field(default=None)
    nc_filename:str = field(default=None)
    output_nc_path:Path = field(default=None)
    mission_start_date:str|None = field(default=None)
    mission_end_date:str|None = field(default=None)
    mission_year:str = field(default=None)
    mission_title:str = field(default=None)
    glider_name:str = field(default=None)
    glider_ids:dict = field(default={'199':'Dora','307':'Reveille','308':'Howdy','540':'Stommel','541':'Sverdrup','1148':'unit_1148'})
    wmo_ids:dict = field(default={'199':'unknown','307':'4801938','308':'4801915','540':'4801916','541':'4801924','1148':'4801915'})

    # Post init variables
    fli_files_loc:Path = field(init=False)
    fli_cache_loc:Path = field(init=False)

    sci_files_loc:Path = field(init=False)
    sci_cache_loc:Path = field(init=False)

    wmo_id:str = field(init=False)

    df_fli:pd.DataFrame = field(init=False)
    ds_fli:xr.Dataset = field(init=False)

    df_sci:pd.DataFrame = field(init=False)
    ds_sci:xr.Dataset = field(init=False)

    ds_mission:xr.Dataset = field(init=False)

    def __attrs_post_init__(self):
        self.get_file_locs()
        self.get_mission_date_range()
        self.get_mission_year_and_glider()
        self.get_wmo_id()
        self.get_mission_title()
        self.get_nc_filename()
        self.get_output_nc_path()
        

    def get_file_locs(self):
        self.fli_files_loc = self.memory_card_copy_loc.joinpath('Flight_card/logs')
        self.fli_cache_loc = self.memory_card_copy_loc.joinpath('Flight_card/state/cache')

        self.sci_files_loc = self.memory_card_copy_loc.joinpath('Science_card/logs')
        self.sci_cache_loc = self.memory_card_copy_loc.joinpath('Science_card/state/cache')

    def get_mission_date_range(self):
        if self.mission_end_date is None:
            self.mission_end_date = str(datetime.datetime.today().date()+datetime.timedelta(days=365))
        if self.mission_start_date is None:
            self.mission_start_date = '2010-01-01'

    def get_mission_year_and_glider(self):
        files = self.get_files(files_loc=self.sci_files_loc,extension='ebd')
        file = files[10]            
        fp = open(file, errors="ignore")
        for line in fp:
            if 'full_filename' in line.strip():
                name = line.replace('full_filename:','').strip()
                self.mission_year = name[name.find('-')+1:find_nth(name,'-',2)].strip()
                self.glider_name = name[:name.find('-')].strip()
                self.glider_name = self.glider_name.replace('unit_','')
                inverted_glider_ids = invert_dict(self.glider_ids)
                # Get the glider_id using the glider_name, sometimes the name given by full_filename is the key and other times its the value
                try:
                    self.glider_name = self.glider_ids[self.glider_name]
                    if self.glider_id is None:
                        self.glider_id = inverted_glider_ids[self.glider_name]
                except KeyError as e:
                    try:
                        self.glider_name = inverted_glider_ids[self.glider_name]
                        if self.glider_id is None:
                            self.glider_id = self.glider_ids[self.glider_name]
                    except KeyError as e:
                        raise ValueError(f'Could not find glider_id, please pass glider_id. Must be one of {list(self.glider_ids.keys())} ({e})')
        # Check if we found the glider_id in the file
        if self.glider_id is None:
            raise ValueError(f'Could not find glider_id, please pass glider_id. Must be one of {list(self.glider_ids.keys())}')
        fp.close()

    def get_mission_title(self):
        if self.mission_title is None:
            self.mission_title = f'Mission {self.mission_num}'

    def get_nc_filename(self):
        if self.nc_filename is None:
            self.nc_filename = f'M{self.mission_num}_{self.mission_year}_{self.glider_id}.nc'

    def get_output_nc_path(self):
        if self.output_nc_path is None:
            output_nc_loc = self.working_dir.joinpath(self.mission_title)
            output_nc_loc.mkdir(exist_ok=True,parents=True)
            self.output_nc_path = output_nc_loc.joinpath(self.nc_filename)
        # If self.output_nc_path is a string
        if isinstance(self.output_nc_path,str):
            self.output_nc_path = Path(self.output_nc_path)
        # Ensure self.output_nc_path is a pathlib.Path object
        if isinstance(self.output_nc_path,Path):
            # If the provided output_nc_path does not specify the filename
            if not self.output_nc_path.is_file():
                self.output_nc_path.joinpath(self.nc_filename)

    def get_wmo_id(self):
        '''Get glider wmo id from glider id and dict of wmo ids'''
        self.wmo_id = self.wmo_ids[self.glider_id]

    def get_files(self,files_loc:Path,extension:str):
        '''Get files to process from files_loc'''
        if files_loc.exists():
            try:
                files = list(files_loc.rglob(f'*.{extension}'))
                files = [str(file) for file in files]
                if len(files) ==0 :
                    raise ValueError(f'No Files found at {files_loc.resolve()}')
            except ValueError:
                files = list(files_loc.rglob(f'*.{extension.upper()}'))
                files = [str(file) for file in files]
                if len(files) ==0 :
                    raise ValueError(f'No Files found at {files_loc.resolve()}')
            return files
        else: 
            raise ValueError(f'Path not found: {files_loc.resolve()}')
        