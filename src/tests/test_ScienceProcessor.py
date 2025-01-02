import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
import pytest
import datetime
import gsw

from glider_ingest.ScienceProcessor import ScienceProcessor
from glider_ingest.MissionData import MissionData

@pytest.fixture
def mission_data():
    return MissionData(
        memory_card_copy_loc=Path("test_data/memory_card"),
        working_dir=Path("test_data/working"),
        mission_num="test123",
        mission_start_date="2023-01-01",
        mission_end_date="2023-12-31",
        glider_id="199"
    )

@pytest.fixture
def science_processor(mission_data):
    return ScienceProcessor(mission_data=mission_data)

@pytest.fixture
def sample_science_df():
    return pd.DataFrame({
        'sci_m_present_time': pd.date_range('2023-01-01', periods=3),
        'sci_water_pressure': [10.0, 20.0, 30.0],
        'sci_water_temp': [25.0, 24.0, 23.0],
        'sci_water_cond': [5.0, 5.1, 5.2],
        'sci_water_sal': [35.0, 35.1, 35.2],
        'sci_water_dens': [1024.0, 1024.1, 1024.2],
        'sci_oxy4_oxygen': [200.0, 195.0, 190.0],
        'sci_flbbcd_bb_units': [0.1, 0.2, 0.3],
        'sci_flbbcd_cdom_units': [2.0, 2.1, 2.2],
        'sci_flbbcd_chlor_units': [0.5, 0.6, 0.7]
    })

def test_get_sci_vars_all_sensors(science_processor):
    variables = ['sci_oxy4_oxygen', 'sci_flbbcd_bb_units', 'sci_water_pressure']
    result = science_processor.get_sci_vars(variables)
    assert len(result) == 7
    assert 'sci_flbbcd_bb_units' in result
    assert 'sci_oxy4_oxygen' in result

def test_get_sci_vars_no_sensors(science_processor):
    variables = ['sci_water_pressure', 'sci_water_temp']
    result = science_processor.get_sci_vars(variables)
    assert len(result) == 3
    assert 'sci_water_pressure' in result
    assert 'sci_water_temp' in result

def test_convert_sci_df_to_ds(science_processor, sample_science_df):
    science_processor.mission_data.df_sci = sample_science_df
    science_processor.convert_sci_df_to_ds()
    assert isinstance(science_processor.mission_data.ds_sci, xr.Dataset)
    assert 'platform' in science_processor.mission_data.ds_sci.variables
    assert 'sci_water_pressure' in science_processor.mission_data.ds_sci.variables

def test_format_sci_ds_with_oxygen(science_processor):
    test_times = pd.date_range('2023-01-01', periods=3)
    test_ds = xr.Dataset({
        'sci_m_present_time': ('index', test_times),
        'sci_water_pressure': ('index', [10.0, 20.0, 30.0]),
        'sci_water_temp': ('index', [25.0, 24.0, 23.0]),
        'sci_water_cond': ('index', [5.0, 5.1, 5.2]),
        'sci_water_sal': ('index', [35.0, 35.1, 35.2]),
        'sci_oxy4_oxygen': ('index', [200.0, 195.0, 190.0])
    })
    science_processor.mission_data.ds_sci = test_ds
    science_processor.format_sci_ds()
    
    assert 'time' in science_processor.mission_data.ds_sci.dims
    assert 'pressure' in science_processor.mission_data.ds_sci.variables
    assert 'temperature' in science_processor.mission_data.ds_sci.variables
    assert 'oxygen' in science_processor.mission_data.ds_sci.variables

def test_add_sci_attrs(science_processor, sample_science_df):
    science_processor.mission_data.df_sci = sample_science_df
    science_processor.convert_sci_df_to_ds()
    science_processor.add_sci_attrs()
    
    assert 'units' in science_processor.mission_data.ds_sci.sci_water_pressure.attrs
    assert 'standard_name' in science_processor.mission_data.ds_sci.sci_water_temp.attrs
    assert 'platform' in science_processor.mission_data.ds_sci.sci_water_cond.attrs
    assert 'update_time' in science_processor.mission_data.ds_sci.sci_water_sal.attrs

def test_process_sci_data_workflow(science_processor, sample_science_df):
    science_processor.mission_data.df_sci = sample_science_df
    science_processor.convert_sci_df_to_ds()
    science_processor.add_sci_attrs()
    science_processor.format_sci_ds()
    
    assert hasattr(science_processor.mission_data, 'ds_sci')
    assert isinstance(science_processor.mission_data.ds_sci, xr.Dataset)
    assert 'temperature' in science_processor.mission_data.ds_sci.variables
    assert 'pressure' in science_processor.mission_data.ds_sci.variables
    assert 'conductivity' in science_processor.mission_data.ds_sci.variables
