import numpy as np
import pandas as pd
import xarray as xr
import uuid
from pathlib import Path
import pytest

from glider_ingest.MissionProcessor import MissionProcessor
from glider_ingest.MissionData import MissionData
from glider_ingest.utils import add_gridded_data, get_polygon_coords

@pytest.fixture
def mission_data():
    return MissionData(
        memory_card_copy_loc=Path("test_data/memory_card"),
        working_dir=Path("test_data/working"),
        mission_num="test123",
        glider_id="199",
        mission_start_date="2023-01-01",
        mission_end_date="2023-12-31"
    )

@pytest.fixture
def mission_processor(mission_data):
    return MissionProcessor(mission_data=mission_data)

@pytest.fixture
def sample_mission_dataset():
    times = pd.date_range('2023-01-01', periods=24, freq='h')
    m_times = pd.date_range('2023-01-01', periods=24, freq='h')
    
    return xr.Dataset({
        'time': times,
        'm_time': m_times,
        'pressure': ('time', np.linspace(0, 100, 24)),
        'temperature': ('time', 20 + np.random.rand(24) * 5),
        'latitude': ('time', 25 + np.random.rand(24) * 0.1),
        'longitude': ('time', -94 + np.random.rand(24) * 0.1),
        'depth': ('time', np.linspace(0, 1000, 24))
    })

def test_add_global_attrs(mission_processor, sample_mission_dataset):
    mission_processor.mission_data.ds_mission = sample_mission_dataset
    mission_processor.add_global_attrs()
    
    attrs = mission_processor.mission_data.ds_mission.attrs
    assert 'Conventions' in attrs
    assert 'creator_email' in attrs
    assert 'date_created' in attrs
    assert 'uuid' in attrs
    assert attrs['platform_type'] == 'Slocum Glider'
    assert attrs['wmo_id'] == mission_processor.mission_data.wmo_id

@pytest.mark.slow
def test_generate_mission_dataset(mission_processor):
    mission_processor.generate_mission_dataset()
    
    assert hasattr(mission_processor.mission_data, 'ds_mission')
    assert isinstance(mission_processor.mission_data.ds_mission, xr.Dataset)
    assert 'time' in mission_processor.mission_data.ds_mission.dims
    assert 'pressure' in mission_processor.mission_data.ds_mission.variables

def test_mission_dataset_variables(mission_processor, sample_mission_dataset):
    mission_processor.mission_data.ds_mission = sample_mission_dataset
    mission_processor.add_global_attrs()
    
    required_attrs = ['title', 'platform_type', 'creator_name', 'date_created']
    for attr in required_attrs:
        assert attr in mission_processor.mission_data.ds_mission.attrs

def test_spatial_bounds_calculation(mission_processor, sample_mission_dataset):
    mission_processor.mission_data.ds_mission = sample_mission_dataset
    mission_processor.add_global_attrs()
    
    attrs = mission_processor.mission_data.ds_mission.attrs
    assert 'geospatial_lat_min' in attrs
    assert 'geospatial_lat_max' in attrs
    assert 'geospatial_lon_min' in attrs
    assert 'geospatial_lon_max' in attrs
    assert 'geospatial_bounds' in attrs

def test_time_coverage_attributes(mission_processor, sample_mission_dataset):
    mission_processor.mission_data.ds_mission = sample_mission_dataset
    mission_processor.add_global_attrs()
    
    attrs = mission_processor.mission_data.ds_mission.attrs
    assert 'time_coverage_start' in attrs
    assert 'time_coverage_end' in attrs
    assert 'time_coverage_duration' in attrs

def test_save_mission_dataset(mission_processor, sample_mission_dataset, tmp_path):
    mission_processor.mission_data.ds_mission = sample_mission_dataset
    mission_processor.mission_data.output_nc_path = tmp_path / "test_mission.nc"
    mission_processor.save_mission_dataset()
    
    assert mission_processor.mission_data.output_nc_path.exists()
    loaded_ds = xr.open_dataset(mission_processor.mission_data.output_nc_path)
    assert isinstance(loaded_ds, xr.Dataset)

@pytest.mark.slow
def test_dataset_integration(mission_processor, sample_mission_dataset):
    mission_processor.mission_data.ds_sci = sample_mission_dataset
    mission_processor.mission_data.ds_fli = sample_mission_dataset
    mission_processor.generate_mission_dataset()
    
    assert 'pressure' in mission_processor.mission_data.ds_mission.variables
    assert 'temperature' in mission_processor.mission_data.ds_mission.variables
    assert 'latitude' in mission_processor.mission_data.ds_mission.variables
    assert 'longitude' in mission_processor.mission_data.ds_mission.variables

def test_uuid_generation(mission_processor, sample_mission_dataset):
    mission_processor.mission_data.ds_mission = sample_mission_dataset
    mission_processor.add_global_attrs()
    
    uuid_str = mission_processor.mission_data.ds_mission.attrs['uuid']
    assert isinstance(uuid.UUID(uuid_str), uuid.UUID)
