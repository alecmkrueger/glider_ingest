import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path
import uuid
from glider_ingest.ingest_science import process_sci_data
from glider_ingest.ingest_flight import process_flight_data
from glider_ingest.utils import add_gridded_data,add_global_attrs,print_time

def get_polygon_coords(ds_mission:xr.Dataset) -> str:
    '''Get the polygon coords for the dataset global attributes'''
    lat_max = np.nanmax(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)
    lat_min = np.nanmin(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)
    lon_max = np.nanmax(ds_mission.longitude.values)
    lon_min = np.nanmin(ds_mission.longitude.values)
    polygon_1 = str(lat_max)+' '+str(ds_mission.longitude[np.where(ds_mission.latitude==lat_max)[0][0]].values) # northmost
    polygon_2 = str(ds_mission.latitude[np.where(ds_mission.longitude==lon_max)[0][0]].values)+' '+str(lon_max) # eastmost
    polygon_3 = str(lat_min)+' '+str(ds_mission.longitude[np.where(ds_mission.latitude==lat_min)[0][0]].values) # southmost
    polygon_4 = str(ds_mission.latitude[np.where(ds_mission.longitude==lon_min)[0][0]].values)+' '+str(lon_min) # westmost
    polygon_5 = polygon_1
    return 'POLYGON (('+polygon_1+' '+polygon_2+' '+polygon_3+' '+polygon_4+' '+polygon_5+'))'

def add_global_attrs(ds_mission:xr.Dataset,mission_title:str,wmo_id:dict) -> xr.Dataset:
    '''Add attributes to the mission dataset'''
    ds_mission.attrs = {'Conventions': 'CF-1.6, COARDS, ACDD-1.3',
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
    'geospatial_lat_resolution': "{:.4e}".format(abs(np.nanmean(np.diff(ds_mission.latitude))))+ ' degree',
    'geospatial_lat_units': 'degree_north',
    'geospatial_lon_resolution': "{:.4e}".format(abs(np.nanmean(np.diff(ds_mission.longitude))))+ ' degree',
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
    'wmo_id': wmo_id,
    'uuid': str(uuid.uuid4()),
    'history': 'dbd and ebd files transferred from dbd2asc on 2023-09-15, merged into single netCDF file on '+pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S'),
    'title': mission_title,
    'source': 'Observational Slocum glider data from source ebd and dbd files',
    'geospatial_lat_min': str(np.nanmin(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)),
    'geospatial_lat_max': str(np.nanmax(ds_mission.latitude[np.where(ds_mission.latitude.values<29.5)].values)),
    'geospatial_lon_min': str(np.nanmin(ds_mission.longitude.values)),
    'geospatial_lon_max': str(np.nanmax(ds_mission.longitude.values)),
    'geospatial_bounds': get_polygon_coords(ds_mission),
    'geospatial_vertical_min': str(np.nanmin(ds_mission.depth[np.where(ds_mission.depth>0)].values)),
    'geospatial_vertical_max': str(np.nanmax(ds_mission.depth.values)),
    'time_coverage_start': str(ds_mission.time[-1].values)[:19],
    'time_coverage_end': str(ds_mission.m_time[-1].values)[:19],
    'time_coverage_duration': 'PT'+str((ds_mission.m_time[-1].values - ds_mission.time[-1].values) / np.timedelta64(1, 's'))+'S'}

    return ds_mission

def combine_flight_science(memory_card_copy_loc,mission_start_date,mission_title,wmo_id,glider_id):
    # Process Science Data
    files = list(Path(f"{memory_card_copy_loc}/Science_card/logs").rglob("*.ebd"))
    files = [str(file) for file in files]
    cache_loc = f"{memory_card_copy_loc}/Science_card/state/cache"
    ds_mission = process_sci_data(files,cache_loc,glider_id=glider_id,wmo_id=wmo_id,mission_start_date=mission_start_date)

    # Process Flight Data
    files = list(Path(f"{memory_card_copy_loc}/Flight_card/logs").rglob("*.dbd"))
    files = [str(file) for file in files]
    cache_loc = f"{memory_card_copy_loc}/Flight_card/state/cache"
    ds_fli = process_flight_data(files,cache_loc,mission_start_date)

    # Add flight data to mission dataset
    ds_mission.update(ds_fli)

    # Add gridded data to mission dataset
    ds_mission = add_gridded_data(ds_mission)

    # Add attributes to the mission dataset
    ds_mission = add_global_attrs(ds_mission,mission_title=mission_title,wmo_id=wmo_id)

    print_time('Finished converting ascii to dataset')

    return ds_mission

# memory_card_copy_loc = "G:/Shared drives/Slocum Gliders/Mission Data & Files/2024 Missions/Mission 46/Memory card copy"
# mission_start_date = '2024-06-17'
# mission_title = 'Mission 46'
# wmo_id = '4801915'
# glider_id = '1148'

# ds_mission = combine_flight_science(memory_card_copy_loc=memory_card_copy_loc,
#                                     mission_start_date=mission_start_date,
#                                     mission_title=mission_title,
#                                     wmo_id=wmo_id,glider_id=glider_id)

# ds_mission.to_netcdf('M46_2024_1148.nc')