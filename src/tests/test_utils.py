import pytest
import numpy as np
import pandas as pd
import xarray as xr
import datetime
from pathlib import Path

from glider_ingest.utils import (
    print_time, 
    find_nth, 
    invert_dict, 
    add_gridded_data, 
    get_polygon_coords
)

def test_print_time(capsys):
    print_time("Test Message")
    captured = capsys.readouterr()
    current_time = datetime.datetime.today().strftime('%H:%M:%S')
    assert f"Test Message: {current_time}" in captured.out

def test_find_nth_basic():
    assert find_nth("hello-world-test", "-", 1) == 5
    assert find_nth("hello-world-test", "-", 2) == 11
    assert find_nth("no-dashes", "-", 1) == 2

def test_find_nth_edge_cases():
    assert find_nth("test", "-", 1) == -1
    assert find_nth("test-string", "-", 3) == -1
    assert find_nth("-start-middle-end", "-", 3) == 13

def test_invert_dict_basic():
    test_dict = {"a": 1, "b": 2, "c": 3}
    inverted = invert_dict(test_dict)
    assert inverted == {1: "a", 2: "b", 3: "c"}

def test_invert_dict_with_duplicates():
    test_dict = {"a": 1, "b": 1, "c": 2}
    inverted = invert_dict(test_dict)
    assert len(inverted) == 2
    assert inverted[2] == "c"

@pytest.fixture
def sample_dataset():
    times = pd.date_range('2023-01-01', periods=24, freq='H')
    return xr.Dataset({
        'time': times,
        'pressure': ('time', np.linspace(0, 100, 24)),
        'temperature': ('time', 20 + np.random.rand(24) * 5),
        'latitude': ('time', np.ones(24) * 25.0),
        'longitude': ('time', np.ones(24) * -94.0)
    })

def test_add_gridded_data(sample_dataset):
    result_ds = add_gridded_data(sample_dataset)
    assert 'g_temp' in result_ds.variables
    assert 'g_pres' in result_ds.dims
    assert 'g_time' in result_ds.dims

def test_get_polygon_coords(sample_dataset):
    polygon_str = get_polygon_coords(sample_dataset)
    assert polygon_str.startswith('POLYGON ((')
    assert polygon_str.endswith('))')
    assert len(polygon_str.split()) == 11  # 5 coordinate pairs plus POLYGON ((

def test_get_polygon_coords_with_varying_coords(sample_dataset):
    sample_dataset['latitude'] = ('time', np.linspace(25.0, 25.5, 24))
    sample_dataset['longitude'] = ('time', np.linspace(-94.0, -94.5, 24))
    polygon_str = get_polygon_coords(sample_dataset)
    coords = polygon_str.replace('POLYGON ((', '').replace('))', '').split(',')
    assert len(coords) == 5  # 5 coordinate pairs

def test_add_gridded_data_attributes(sample_dataset):
    result_ds = add_gridded_data(sample_dataset)
    assert 'units' in result_ds.g_temp.attrs
    assert 'standard_name' in result_ds.g_temp.attrs
    assert 'valid_min' in result_ds.g_temp.attrs
    assert 'valid_max' in result_ds.g_temp.attrs

def test_add_gridded_data_dimensions(sample_dataset):
    result_ds = add_gridded_data(sample_dataset)
    assert len(result_ds.g_time) > 0
    assert len(result_ds.g_pres) > 0
    assert result_ds.g_temp.shape == (len(result_ds.g_time), len(result_ds.g_pres))

def test_get_polygon_coords_latitude_filtering(sample_dataset):
    sample_dataset['latitude'] = ('time', np.concatenate([
        np.ones(12) * 25.0,
        np.ones(12) * 30.0
    ]))
    polygon_str = get_polygon_coords(sample_dataset)
    assert polygon_str.startswith('POLYGON ((')
    assert '30.0' not in polygon_str  # Values >= 29.5 should be filtered
