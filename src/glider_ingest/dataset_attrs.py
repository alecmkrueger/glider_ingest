from glider_ingest.variable import Variable
from glider_ingest.utils import get_polygon_coords,get_polygon_bounds

import numpy as np 
import pandas as pd
import uuid

# Flight Variables
def get_default_variables():
    m_pressure = Variable(
        data_source_name='m_pressure',
        short_name='m_pressure',
        accuracy=0.01,
        ancillary_variables='',
        axis='Z',
        bytes=4,
        comment='Alias for m_pressure',
        long_name='GPS Pressure',
        observation_type='measured',
        platform='platform',
        positive='down',
        precision=0.01,
        reference_datum='sea-surface',
        resolution=0.01,
        source_sensor='sci_water_pressure',
        standard_name='sea_water_pressure',
        units='bar',
        valid_max=2000.0,
        valid_min=0.0,
    )

    m_water_depth = Variable(
        data_source_name='m_water_depth',
        short_name='depth',
        accuracy=0.01,
        ancillary_variables='',
        axis='Z',
        bytes=4,
        comment='Alias for m_depth',
        long_name='GPS Depth',
        observation_type='calculated',
        platform='platform',
        positive='down',
        precision=0.01,
        reference_datum='sea-surface',
        resolution=0.01,
        source_sensor='m_depth',
        standard_name='sea_water_depth',
        units='meters',
        valid_max=2000.0,
        valid_min=0.0,
    )

    m_latitude = Variable(
        data_source_name='m_lat',
        short_name='latitude',
        ancillary_variables='',
        axis='Y',
        bytes=8,
        comment='m_gps_lat converted to decimal degrees and interpolated',
        coordinate_reference_frame='urn:ogc:crs:EPSG::4326',
        long_name='Latitude',
        observation_type='calculated',
        platform='platform',
        precision=5,
        reference_datum='WGS84',
        source_sensor='m_gps_lat',
        standard_name='latitude',
        units='degree_north',
        valid_max=90.0,
        valid_min=-90.0,
    )

    m_longitude = Variable(
        data_source_name='m_lon',
        short_name='longitude',
        ancillary_variables='',
        axis='X',
        bytes=8,
        comment='m_gps_lon converted to decimal degrees and interpolated',
        coordinate_reference_frame='urn:ogc:crs:EPSG::4326',
        long_name='Longitude',
        observation_type='calculated',
        platform='platform',
        precision=5,
        reference_datum='WGS84',
        source_sensor='m_gps_lon',
        standard_name='longitude',
        units='degree_east',
        valid_max=180.0,
        valid_min=-180.0,
    )

    # Science Variables

    sci_water_pressure = Variable(
        data_source_name='sci_water_pressure',
        short_name='pressure',
        accuracy=0.01,
        ancillary_variables='',
        axis='Z',
        bytes=4,
        comment='Alias for sci_water_pressure',
        instrument='instrument_ctd',
        long_name='CTD Pressure',
        observation_type='measured',
        platform='platform',
        positive='down',
        precision=0.01,
        reference_datum='sea-surface',
        resolution=0.01,
        source_sensor='sci_water_pressure',
        standard_name='sea_water_pressure',
        units='bar',
        valid_max=2000.0,
        valid_min=0.0,
    )

    sci_water_temp = Variable(
        data_source_name='sci_water_temp',
        short_name='temperature',
        accuracy=0.004,
        ancillary_variables='',
        bytes=4,
        instrument='instrument_ctd',
        long_name='Temperature',
        observation_type='measured',
        platform='platform',
        precision=0.001,
        resolution=0.001,
        standard_name='sea_water_temperature',
        units='Celsius',
        valid_max=40.0,
        valid_min=-5.0,
        to_grid=True
    )

    sci_water_cond = Variable(
        data_source_name='sci_water_cond',
        short_name='conductivity',
        accuracy=0.001,
        ancillary_variables='',
        bytes=4,
        instrument='instrument_ctd',
        long_name='sci_water_cond',
        observation_type='measured',
        platform='platform',
        precision=1e-05,
        resolution=1e-05,
        standard_name='sea_water_electrical_conductivity',
        units='S m-1',
        valid_max=10.0,
        valid_min=0.0,
        to_grid=True
    )

    sci_water_sal = Variable(
        data_source_name=None,
        short_name='salinity',
        accuracy='',
        ancillary_variables='',
        instrument='instrument_ctd',
        long_name='Salinity',
        observation_type='calculated',
        platform='platform',
        precision='',
        resolution='',
        standard_name='sea_water_practical_salinity',
        units='1',
        valid_max=40.0,
        valid_min=0.0,
        to_grid=True
    )

    sci_water_dens = Variable(
        data_source_name=None,
        short_name='density',
        accuracy='',
        ancillary_variables='',
        instrument='instrument_ctd',
        long_name='Density',
        observation_type='calculated',
        platform='platform',
        precision='',
        resolution='',
        standard_name='sea_water_density',
        units='kg m-3',
        valid_max=1040.0,
        valid_min=1015.0,
        to_grid=True
    )

    sci_flbbcd_bb_units = Variable(
        data_source_name='sci_flbbcd_bb_units',
        short_name='turbidity',
        accuracy='',
        ancillary_variables='',
        instrument='instrument_flbbcd',
        long_name='Turbidity',
        observation_type='calculated',
        platform='platform',
        precision='',
        resolution='',
        standard_name='sea_water_turbidity',
        units='1',
        valid_max=1.0,
        valid_min=0.0,
        to_grid=True
    )

    sci_flbbcd_cdom_units = Variable(
        data_source_name='sci_flbbcd_cdom_units',
        short_name='cdom',
        accuracy='',
        ancillary_variables='',
        instrument='instrument_flbbcd',
        long_name='CDOM',
        observation_type='calculated',
        platform='platform',
        precision='',
        resolution='',
        standard_name='concentration_of_colored_dissolved_organic_matter_in_sea_water',
        units='ppb',
        valid_max=50.0,
        valid_min=0.0,
        to_grid=True
    )

    sci_flbbcd_chlor_units = Variable(
        data_source_name='sci_flbbcd_chlor_units',
        short_name='chlorophyll',
        accuracy='',
        ancillary_variables='',
        instrument='instrument_flbbcd',
        long_name='Chlorophyll_a',
        observation_type='calculated',
        platform='platform',
        precision='',
        resolution='',
        standard_name='mass_concentration_of_chlorophyll_a_in_sea_water',
        units='\u03BCg/L',
        valid_max=10.0,
        valid_min=0.0,
        to_grid=True
    )

    sci_oxy4_oxygen = Variable(
        data_source_name='sci_oxy4_oxygen',
        short_name='oxygen',
        accuracy='',
        ancillary_variables='',
        instrument='instrument_ctd_modular_do_sensor',
        long_name='oxygen',
        observation_type='calculated',
        platform='platform',
        precision='',
        resolution='',
        standard_name='moles_of_oxygen_per_unit_mass_in_sea_water',
        units='\u03BCmol/kg',
        valid_max=500.0,
        valid_min=0.0,
        to_grid=True
    )
    
    default_variables = [
        m_pressure,
        m_water_depth,
        m_latitude,
        m_longitude,
        sci_water_pressure,
        sci_water_temp,
        sci_water_cond,
        sci_water_sal,
        sci_water_dens,
        sci_flbbcd_bb_units,
        sci_flbbcd_cdom_units,
        sci_flbbcd_chlor_units,
        sci_oxy4_oxygen
    ]
    
    return default_variables

def get_global_attrs(wmo_id:str,mission_title:str,longitude:np.ndarray,latitude:np.ndarray,depth:np.ndarray,time:np.ndarray):
    
    # Calculate spatial bounds and resolution
    lat_max, lat_min, lon_max, lon_min = get_polygon_bounds(latitude=latitude, longitude=longitude)
    geospatial_bounds = get_polygon_coords(longitude=longitude, latitude=latitude,
                                           lat_max=lat_max, lat_min=lat_min, lon_max=lon_max, lon_min=lon_min)
    
    geospatial_lat_resolution = "{:.4e}".format(abs(np.nanmean(np.diff(latitude))))+ ' degree'
    geospatial_lon_resolution = "{:.4e}".format(abs(np.nanmean(np.diff(longitude))))+ ' degree'
    
    vertical_min = np.nanmin(depth[np.where(depth>0)])
    vertical_max = np.nanmax(depth)
    
    # Get current time
    current_time = pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')
    # Get dataset time range
    time_coverage_start = time[-1]
    time_coverage_end = time[-1]
    time_coverage_duration = f"PT{str((time_coverage_end - time_coverage_start) / np.timedelta64(1, 's'))}S"
    
    # Get uuid
    uuid_str = str(uuid.uuid4())
    
    
    {'Conventions': 'CF-1.6, COARDS, ACDD-1.3',
    'acknowledgment': ' ',
    'cdm_data_type': 'Profile',
    'comment': 'time is the ctd_time from sci_m_present_time, g_time and g_pres are the grided time and pressure',
    'contributor_name': 'Steven F. DiMarco',
    'contributor_role': ' ',
    'creator_email': 'sakib@tamu.edu, gexiao@tamu.edu',
    'creator_institution': 'Texas A&M University, Geochemical and Environmental Research Group',
    'creator_name': 'Sakib Mahmud, Xiao Ge',
    'creator_type': 'persons',
    'creator_url': 'https://gerg.tamu.edu/',
    'date_created': current_time,
    'date_issued': current_time,
    'date_metadata_modified': '2023-09-15',
    'date_modified': current_time,
    'deployment': ' ',
    'featureType': 'profile',
    'geospatial_bounds_crs': 'EPSG:4326',
    'geospatial_bounds_vertical_crs': 'EPSG:5831',
    'geospatial_lat_resolution': geospatial_lat_resolution,
    'geospatial_lat_units': 'degree_north',
    'geospatial_lon_resolution': geospatial_lon_resolution,
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
    'uuid': uuid_str,
    'history': 'dbd and ebd files transferred from dbd2asc on 2023-09-15, merged into single netCDF file on '+current_time,
    'title': mission_title,
    'source': 'Observational Slocum glider data from source ebd and dbd files',
    'geospatial_lat_min': str(lat_min),
    'geospatial_lat_max': str(lat_max),
    'geospatial_lon_min': str(lon_min),
    'geospatial_lon_max': str(lon_max),
    'geospatial_bounds': geospatial_bounds,
    'geospatial_vertical_min': str(vertical_min),
    'geospatial_vertical_max': str(vertical_max),
    'time_coverage_start': str(time_coverage_start)[:19],
    'time_coverage_end': str(time_coverage_end)[:19],
    'time_coverage_duration': time_coverage_duration}