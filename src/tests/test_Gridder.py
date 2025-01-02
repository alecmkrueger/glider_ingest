import numpy as np
import pandas as pd
import xarray as xr
import gsw
import pytest
from datetime import datetime

from glider_ingest.Gridder import Gridder

@pytest.fixture
def sample_mission_dataset():
    times = pd.date_range('2023-01-01', periods=24, freq='H')
    pressures = np.linspace(0, 100, 50)
    temperatures = 20 + np.random.rand(len(times), len(pressures)) * 5
    salinities = 35 + np.random.rand(len(times), len(pressures))
    
    return xr.Dataset({
        'time': times,
        'pressure': ('time', pressures),
        'temperature': (('time', 'pressure'), temperatures),
        'salinity': (('time', 'pressure'), salinities),
        'conductivity': (('time', 'pressure'), np.ones_like(temperatures) * 5),
        'density': (('time', 'pressure'), np.ones_like(temperatures) * 1025),
        'latitude': ('time', np.ones_like(times) * 25.0),
        'longitude': ('time', np.ones_like(times) * -94.0)
    })

@pytest.fixture
def gridder(sample_mission_dataset):
    return Gridder(ds_mission=sample_mission_dataset, interval_h=1, interval_p=0.5)

def test_gridder_initialization(gridder):
    assert gridder.interval_h == 1
    assert gridder.interval_p == 0.5
    assert isinstance(gridder.ds, xr.Dataset)
    assert hasattr(gridder, 'time')
    assert hasattr(gridder, 'pres')

def test_initialize_grid(gridder):
    assert hasattr(gridder, 'int_time')
    assert hasattr(gridder, 'int_pres')
    assert hasattr(gridder, 'grid_pres')
    assert hasattr(gridder, 'grid_time')
    assert isinstance(gridder.data_arrays, dict)

def test_grid_dimensions(gridder):
    gridder.create_gridded_dataset()
    assert 'g_time' in gridder.ds_gridded.dims
    assert 'g_pres' in gridder.ds_gridded.dims
    expected_pres_points = int((np.nanmax(gridder.pres) - 0) / gridder.interval_p)
    assert len(gridder.ds_gridded.g_pres) <= expected_pres_points + 1

def test_gridded_variables(gridder):
    gridder.create_gridded_dataset()
    assert 'g_temp' in gridder.ds_gridded.variables
    assert 'g_salt' in gridder.ds_gridded.variables
    assert 'g_dens' in gridder.ds_gridded.variables
    assert 'g_depth' in gridder.ds_gridded.variables

def test_calculated_variables(gridder):
    gridder.create_gridded_dataset()
    assert 'g_hc' in gridder.ds_gridded.variables
    assert 'g_phc' in gridder.ds_gridded.variables
    assert 'g_sp' in gridder.ds_gridded.variables
    
    # Validate heat content calculations
    assert not np.any(gridder.ds_gridded.g_hc < 0)
    assert not np.any(gridder.ds_gridded.g_phc < 0)

def test_attribute_preservation(gridder):
    gridder.create_gridded_dataset()
    assert 'units' in gridder.ds_gridded.g_temp.attrs
    assert 'standard_name' in gridder.ds_gridded.g_salt.attrs
    assert 'valid_min' in gridder.ds_gridded.g_dens.attrs
    assert 'valid_max' in gridder.ds_gridded.g_depth.attrs

def test_interpolation_handling(gridder):
    gridder.create_gridded_dataset()
    # Check for NaN handling at edges
    assert np.any(np.isnan(gridder.ds_gridded.g_temp[:, 0]))
    assert np.any(np.isnan(gridder.ds_gridded.g_temp[:, -1]))
    
    # Check interpolation is within bounds of input data
    assert np.nanmax(gridder.ds_gridded.g_temp) <= np.nanmax(gridder.ds.temperature)
    assert np.nanmin(gridder.ds_gridded.g_temp) >= np.nanmin(gridder.ds.temperature)

def test_custom_grid_intervals():
    ds = sample_mission_dataset()
    custom_gridder = Gridder(ds_mission=ds, interval_h=2, interval_p=1.0)
    custom_gridder.create_gridded_dataset()
    
    standard_gridder = Gridder(ds_mission=ds, interval_h=1, interval_p=0.5)
    standard_gridder.create_gridded_dataset()
    
    assert len(custom_gridder.ds_gridded.g_time) < len(standard_gridder.ds_gridded.g_time)
    assert len(custom_gridder.ds_gridded.g_pres) < len(standard_gridder.ds_gridded.g_pres)
