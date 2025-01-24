import unittest
import numpy as np
import pandas as pd
import xarray as xr
from glider_ingest.gridder import Gridder

class TestGridder(unittest.TestCase):
    def setUp(self):
        # Create sample dataset for testing
        times = pd.date_range('2023-01-01', periods=24, freq='h')
        pressures = np.linspace(0, 100, 24)
        temps = np.random.uniform(20, 25, 24)
        salts = np.random.uniform(35, 36, 24)
        lats = np.linspace(20, 29, 24)
        lons = np.linspace(-98, -80, 24)
        
        self.test_ds = xr.Dataset(
            data_vars={
                'pressure': ('time', pressures),
                'temperature': ('time', temps),
                'salinity': ('time', salts),
                'conductivity': ('time', np.random.uniform(3, 4, 24)),
                'density': ('time', np.random.uniform(1020, 1025, 24)),
                'oxygen': ('time', np.random.uniform(180, 220, 24)),
                'latitude': ('time', lats),
                'longitude': ('time', lons)
            },
            coords={'time': times}
        )

    def test_initialization(self):
        gridder = Gridder(self.test_ds, interval_h=1, interval_p=0.1)
        self.assertEqual(gridder.interval_h, 1)
        self.assertEqual(gridder.interval_p, 0.1)
        self.assertIsInstance(gridder.ds, xr.Dataset)

    def test_grid_initialization(self):
        gridder = Gridder(self.test_ds)
        self.assertIsNotNone(gridder.int_time)
        self.assertIsNotNone(gridder.int_pres)
        self.assertTrue(len(gridder.int_pres) > 0)
        self.assertTrue(len(gridder.int_time) > 0)

    def test_custom_intervals(self):
        gridder = Gridder(self.test_ds, interval_h=2, interval_p=0.5)
        self.assertEqual(gridder.interval_h, 2)
        self.assertEqual(gridder.interval_p, 0.5)

    def test_missing_data_handling(self):
        # Create dataset with some NaN values
        ds_with_nans = self.test_ds.copy()
        ds_with_nans['pressure'][0:5] = np.nan
        gridder = Gridder(ds_with_nans)
        self.assertLess(len(gridder.ds.time), len(ds_with_nans.time))

    def test_gridded_dataset_creation(self):
        gridder = Gridder(self.test_ds)
        gridder.create_gridded_dataset()
        
        required_vars = ['g_temp', 'g_salt', 'g_cond', 'g_dens', 'g_oxy4', 
                        'g_hc', 'g_phc', 'g_sp', 'g_depth']
        
        for var in required_vars:
            self.assertIn(var, gridder.ds_gridded.data_vars)
            self.assertIn('g_time', gridder.ds_gridded[var].dims)
            self.assertIn('g_pres', gridder.ds_gridded[var].dims)

    def test_attributes_addition(self):
        gridder = Gridder(self.test_ds)
        gridder.create_gridded_dataset()
        
        # Verify attributes are added correctly
        self.assertIn('long_name', gridder.ds_gridded['g_temp'].attrs)
        self.assertIn('units', gridder.ds_gridded['g_temp'].attrs)
        self.assertIn('update_time', gridder.ds_gridded['g_temp'].attrs)

    def test_edge_case_single_timepoint(self):
        single_time_ds = self.test_ds.isel(time=[0])
        with self.assertRaises(ValueError):
            Gridder(single_time_ds)

    def test_pressure_range_validation(self):
        gridder = Gridder(self.test_ds)
        self.assertTrue(np.all(gridder.int_pres >= 0))
        self.assertTrue(np.all(gridder.int_pres <= np.nanmax(self.test_ds.pressure)))
