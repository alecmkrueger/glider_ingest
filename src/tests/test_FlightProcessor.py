import pandas as pd
import xarray as xr
from pathlib import Path
import pytest

from glider_ingest.FlightProcessor import FlightProcessor
from glider_ingest.MissionData import MissionData

@pytest.fixture
def mission_data():
    return MissionData(
        memory_card_copy_loc=Path("test_data/memory_card"),
        working_dir=Path("test_data/working"),
        mission_num="test123",
        mission_start_date="2023-01-01",
        mission_end_date="2023-12-31"
    )

@pytest.fixture
def flight_processor(mission_data):
    return FlightProcessor(mission_data=mission_data)

@pytest.fixture
def sample_flight_df():
    return pd.DataFrame({
        'm_present_time': pd.date_range('2023-01-01', periods=3),
        'm_lat': [25.1, 25.2, 25.3],
        'm_lon': [-94.1, -94.2, -94.3],
        'm_pressure': [10.0, 20.0, 30.0],
        'm_water_depth': [100.0, 200.0, 300.0]
    })

def test_convert_fli_df_to_ds(flight_processor, sample_flight_df):
    flight_processor.mission_data.df_fli = sample_flight_df
    flight_processor.convert_fli_df_to_ds()
    assert isinstance(flight_processor.mission_data.ds_fli, xr.Dataset)
    assert 'm_pressure' in flight_processor.mission_data.ds_fli.variables

def test_format_flight_ds(flight_processor):
    test_times = pd.date_range('2023-01-01', periods=3)
    test_ds = xr.Dataset({
        'm_present_time': ('index', test_times),
        'm_pressure': ('index', [10.0, 20.0, 30.0]),
        'm_water_depth': ('index', [100.0, 200.0, 300.0]),
        'm_latitude': ('index', [25.1, 25.2, 25.3]),
        'm_longitude': ('index', [-94.1, -94.2, -94.3])
    })
    flight_processor.mission_data.ds_fli = test_ds
    flight_processor.format_flight_ds()
    
    assert 'm_time' in flight_processor.mission_data.ds_fli.dims
    assert 'depth' in flight_processor.mission_data.ds_fli.variables
    assert 'latitude' in flight_processor.mission_data.ds_fli.variables
    assert 'longitude' in flight_processor.mission_data.ds_fli.variables

def test_add_flight_attrs(flight_processor):
    test_ds = xr.Dataset({
        'm_pressure': ('time', [10.0, 20.0]),
        'm_water_depth': ('time', [100.0, 200.0]),
        'm_latitude': ('time', [25.1, 25.2]),
        'm_longitude': ('time', [-94.1, -94.2])
    })
    flight_processor.mission_data.ds_fli = test_ds
    flight_processor.add_flight_attrs()
    
    assert 'units' in flight_processor.mission_data.ds_fli.m_pressure.attrs
    assert 'standard_name' in flight_processor.mission_data.ds_fli.m_latitude.attrs
    assert 'axis' in flight_processor.mission_data.ds_fli.m_longitude.attrs
    assert 'update_time' in flight_processor.mission_data.ds_fli.m_water_depth.attrs

@pytest.mark.slow
def test_process_flight_data_workflow(flight_processor, sample_flight_df):
    flight_processor.mission_data.df_fli = sample_flight_df
    flight_processor.process_flight_data()
    
    assert hasattr(flight_processor.mission_data, 'ds_fli')
    assert isinstance(flight_processor.mission_data.ds_fli, xr.Dataset)
    assert 'latitude' in flight_processor.mission_data.ds_fli.variables
    assert 'longitude' in flight_processor.mission_data.ds_fli.variables
    assert 'depth' in flight_processor.mission_data.ds_fli.variables
