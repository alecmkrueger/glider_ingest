import numpy as np
import pandas as pd
import xarray as xr
import uuid
from attrs import define,field
from pathlib import Path

from glider_ingest.MissionData import MissionData
from glider_ingest.ScienceProcessor import ScienceProcessor
from glider_ingest.FlightProcessor import FlightProcessor
from glider_ingest.utils import add_gridded_data,get_polygon_coords


@define
class MissionProcessor:

    mission_data:MissionData

    def add_global_attrs(self) -> xr.Dataset:
        '''Add attributes to the mission dataset'''
        self.mission_data.ds_mission.attrs = {'Conventions': 'CF-1.6, COARDS, ACDD-1.3',
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
        'geospatial_lat_resolution': "{:.4e}".format(abs(np.nanmean(np.diff(self.mission_data.ds_mission.latitude))))+ ' degree',
        'geospatial_lat_units': 'degree_north',
        'geospatial_lon_resolution': "{:.4e}".format(abs(np.nanmean(np.diff(self.mission_data.ds_mission.longitude))))+ ' degree',
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
        'wmo_id': self.mission_data.wmo_id,
        'uuid': str(uuid.uuid4()),
        'history': 'dbd and ebd files transferred from dbd2asc on 2023-09-15, merged into single netCDF file on '+pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
        'title': self.mission_data.mission_title,
        'source': 'Observational Slocum glider data from source ebd and dbd files',
        'geospatial_lat_min': str(np.nanmin(self.mission_data.ds_mission.latitude[np.where(self.mission_data.ds_mission.latitude.values<29.5)].values)),
        'geospatial_lat_max': str(np.nanmax(self.mission_data.ds_mission.latitude[np.where(self.mission_data.ds_mission.latitude.values<29.5)].values)),
        'geospatial_lon_min': str(np.nanmin(self.mission_data.ds_mission.longitude.values)),
        'geospatial_lon_max': str(np.nanmax(self.mission_data.ds_mission.longitude.values)),
        'geospatial_bounds': get_polygon_coords(self.mission_data.ds_mission),
        'geospatial_vertical_min': str(np.nanmin(self.mission_data.ds_mission.depth[np.where(self.mission_data.ds_mission.depth>0)].values)),
        'geospatial_vertical_max': str(np.nanmax(self.mission_data.ds_mission.depth.values)),
        'time_coverage_start': str(self.mission_data.ds_mission.time[-1].values)[:19],
        'time_coverage_end': str(self.mission_data.ds_mission.m_time[-1].values)[:19],
        'time_coverage_duration': 'PT'+str((self.mission_data.ds_mission.m_time[-1].values - self.mission_data.ds_mission.time[-1].values) / np.timedelta64(1, 's'))+'S'}


    def process_sci(self):
        sci_processor = ScienceProcessor(mission_data=self.mission_data)
        sci_processor.process_sci_data()
        return sci_processor.mission_data

    def process_fli(self):
        fli_processor = FlightProcessor(mission_data=self.mission_data)
        fli_processor.process_flight_data()
        return fli_processor.mission_data
    
    def generate_mission_dataset(self):
        self.mission_data = self.process_sci()
        self.mission_data = self.process_fli()

        # Combine sci and fli datasets
        self.mission_data.ds_mission = self.mission_data.ds_sci.copy()
        self.mission_data.ds_mission.update(self.mission_data.ds_fli)

        # Add gridded data to mission dataset
        self.mission_data.ds_mission = add_gridded_data(self.mission_data.ds_mission)

        # Add attributes to the mission dataset
        self.add_global_attrs()

    def save_mission_dataset(self):
        if not hasattr(self.mission_data,'ds_mission'):
            self.generate_mission_dataset()
        self.mission_data.ds_mission.to_netcdf(self.mission_data.output_nc_path,engine='netcdf4')
