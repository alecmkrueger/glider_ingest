import pandas as pd
import xarray as xr
from pathlib import Path
from attrs import define,field
import datetime

from glider_ingest.utils import find_nth

@define
class MissionData:
    # Required Variables
    memory_card_copy_loc:Path
    working_dir:Path
    mission_num:str
    glider_id:str

    # Optional Variables
    nc_filename:str = field(default=None)
    output_nc_path:Path = field(default=None)
    mission_start_date:str|None = field(default=None)
    mission_end_date:str|None = field(default=None)
    mission_year:str = field(default=None)
    glider_ids:dict = field(default={'199':'Dora','307':'Reveille','308':'Howdy','540':'Stommel','541':'Sverdrup','1148':'unit_1148'})
    glider_ids_invert:dict =  field(default={'Dora': '199', 'Reveille': '307', 'Howdy': '308', 'Stommel': '540', 'Sverdrup': '541', 'unit_1148': '1148'})
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
        self.get_glider_id()
        self.get_wmo_id()

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

    def get_mission_year(self):
        files = self.get_sci_files('dbd')
        file = files[0]
        fp = open(file, errors="ignore")
        for i, line in enumerate(fp):
            if i==5:
                name = line.replace('full_filename:','').strip()
                year = name[name.find('-')+1:find_nth(name,'-',2)].strip()
                name = name[:name.find('-')].strip()
                print(f'{name = }')
                print(f'{year = }')
            if i>5:
                break
        fp.close()

    def get_nc_filename(self):
        if self.nc_filename is None:
            self.get_mission_year()
            self.nc_filename = f'M{self.mission_num}_{self.mission_year}_{self.glider_id}.nc'

    def get_output_nc_path(self):
        if self.output_nc_path is None:
            self.get_nc_filename()
            self.output_nc_path = self.working_dir.joinpath(self.mission_num,self.nc_filename)
        # Ensure self.output_nc_path is a pathlib.Path object
        elif isinstance(self.output_nc_path,Path):
            # If the provided output_nc_path does not specify the filename
            if not self.output_nc_path.is_file():
                # Make sure we have the nc_filename attribute
                self.get_nc_filename()
                self.output_nc_path.joinpath(self.nc_filename)

    def get_glider_id(self):
        '''Get glider id from dbd files if possible'''

    def get_wmo_id(self):
        '''Get glider wmo id from glider id and dict of wmo ids'''
        self.wmo_id = self.wmo_ids[self.glider_id]

    def get_fli_files(self,extension):
        '''Get files to process from files_loc'''
        if self.fli_files_loc.exists():
            files = self.fli_files_loc.rglob(f'*.{extension}')
            files = [str(file) for file in files]
            return files
        else: 
            raise ValueError(f'Invaid path for files: {self.files_loc}')

    def get_sci_files(self,extension):
        '''Get files to process from files_loc'''
        if self.sci_files_loc.exists():
            files = self.sci_files_loc.rglob(f'*.{extension}')
            files = [str(file) for file in files]
            return files
        else: 
            raise ValueError(f'Invaid path for files: {self.files_loc}')
        