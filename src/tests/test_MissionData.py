import pytest
import pandas as pd
import xarray as xr
from pathlib import Path
import datetime

from glider_ingest.MissionData import MissionData
from glider_ingest.utils import find_nth, invert_dict

@pytest.fixture
def base_mission_data():
    return MissionData(
        memory_card_copy_loc=Path("test_data/memory_card"),
        working_dir=Path("test_data/working"),
        mission_num="test123"
    )

def test_mission_data_initialization(base_mission_data):
    assert base_mission_data.mission_num == "test123"
    assert isinstance(base_mission_data.memory_card_copy_loc, Path)
    assert isinstance(base_mission_data.working_dir, Path)

def test_get_file_locs(base_mission_data):
    base_mission_data.get_file_locs()
    assert base_mission_data.fli_files_loc.name == "logs"
    assert base_mission_data.sci_files_loc.name == "logs"
    assert base_mission_data.fli_cache_loc.name == "cache"
    assert base_mission_data.sci_cache_loc.name == "cache"

def test_get_mission_date_range_defaults(base_mission_data):
    base_mission_data.get_mission_date_range()
    assert base_mission_data.mission_start_date == "2010-01-01"
    assert datetime.datetime.strptime(base_mission_data.mission_end_date, "%Y-%m-%d")

def test_get_mission_date_range_custom():
    mission_data = MissionData(
        memory_card_copy_loc=Path("test_data/memory_card"),
        working_dir=Path("test_data/working"),
        mission_num="test123",
        mission_start_date="2023-01-01",
        mission_end_date="2023-12-31"
    )
    assert mission_data.mission_start_date == "2023-01-01"
    assert mission_data.mission_end_date == "2023-12-31"

def test_get_wmo_id(base_mission_data):
    base_mission_data.glider_id = "199"
    base_mission_data.get_wmo_id()
    assert base_mission_data.wmo_id == "unknown"

def test_get_mission_title(base_mission_data):
    base_mission_data.get_mission_title()
    assert base_mission_data.mission_title == f"Mission {base_mission_data.mission_num}"

def test_get_nc_filename():
    mission_data = MissionData(
        memory_card_copy_loc=Path("test_data/memory_card"),
        working_dir=Path("test_data/working"),
        mission_num="test123",
        glider_id="199",
        mission_year="2023"
    )
    mission_data.get_nc_filename()
    assert mission_data.nc_filename == "Mtest123_2023_199.nc"

def test_get_output_nc_path(base_mission_data):
    base_mission_data.mission_title = "TestMission"
    base_mission_data.nc_filename = "test.nc"
    base_mission_data.get_output_nc_path()
    assert base_mission_data.output_nc_path.parent.name == "TestMission"
    assert base_mission_data.output_nc_path.name == "test.nc"

def test_custom_output_nc_path():
    mission_data = MissionData(
        memory_card_copy_loc=Path("test_data/memory_card"),
        working_dir=Path("test_data/working"),
        mission_num="test123",
        output_nc_path=Path("custom/output/path.nc")
    )
    assert mission_data.output_nc_path == Path("custom/output/path.nc")

def test_glider_id_mapping(base_mission_data):
    base_mission_data.glider_id = "199"
    assert base_mission_data.glider_ids[base_mission_data.glider_id] == "Dora"
    
def test_wmo_id_mapping(base_mission_data):
    base_mission_data.glider_id = "307"
    base_mission_data.get_wmo_id()
    assert base_mission_data.wmo_id == "4801938"

def test_get_files_validation(base_mission_data):
    with pytest.raises(ValueError, match="Invaid path for files"):
        base_mission_data.get_files(Path("nonexistent/path"), "ebd")

def test_mission_year_extraction(base_mission_data):
    base_mission_data.mission_year = "2023"
    base_mission_data.get_mission_title()
    base_mission_data.get_nc_filename()
    assert "2023" in base_mission_data.nc_filename

def test_glider_name_conversion(base_mission_data):
    base_mission_data.glider_id = "199"
    base_mission_data.glider_name = "Dora"
    inverted = invert_dict(base_mission_data.glider_ids)
    assert inverted[base_mission_data.glider_name] == base_mission_data.glider_id
