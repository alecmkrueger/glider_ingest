import unittest
import numpy as np
import xarray as xr
from pathlib import Path
from glider_ingest.gridder import Gridder

class TestGridder(unittest.TestCase):
    def setUp(self):
        # Create test dataset with known valid values
        times = np.array(['2023-01-01T00:00:00', '2023-01-01T01:00:00'], dtype='datetime64[ns]')
        pressure = np.array([0.0, 10.0])
        temperature = np.array([20.0, 18.0])
        salinity = np.array([35.0, 35.2])
        density = np.array([1024.0, 1025.0])

        self.test_dataset = xr.Dataset(
            data_vars={
                'pressure': ('time', pressure),
                'temperature': ('time', temperature, {'to_grid': True}),
                'salinity': ('time', salinity, {'to_grid': True}),
                'density': ('time', density, {'to_grid': True}),
                'longitude': ('time', np.array([120.0, 120.0])),
                'latitude': ('time', np.array([-20.0, -20.0])),
            },
            coords={'time': times}
        )

    def test_gridder_initialization(self):
        gridder = Gridder(ds_mission=self.test_dataset)
        self.assertIsInstance(gridder, Gridder)
        self.assertEqual(gridder.interval_h, 1)
        self.assertEqual(gridder.interval_p, 0.1)

    def test_check_len(self):
        gridder = Gridder(ds_mission=self.test_dataset)
        valid_array = np.array([1, 2, 3])
        with self.assertRaises(ValueError):
            gridder.check_len([], 0)
        self.assertIsNone(gridder.check_len(valid_array, 1))

    def test_initialize_grid(self):
        gridder = Gridder(ds_mission=self.test_dataset)
        self.assertIsNotNone(gridder.grid_pres)
        self.assertIsNotNone(gridder.grid_time)
        self.assertTrue('int_temperature' in gridder.data_arrays)
        self.assertTrue('int_salinity' in gridder.data_arrays)

    def test_create_gridded_dataset(self):
        gridder = Gridder(ds_mission=self.test_dataset)
        gridder.create_gridded_dataset()

        self.assertIsInstance(gridder.ds_gridded, xr.Dataset)
        self.assertIn('g_temperature', gridder.ds_gridded)
        self.assertIn('g_salinity', gridder.ds_gridded)
        self.assertIn('g_depth', gridder.ds_gridded)
        self.assertIn('g_sp', gridder.ds_gridded)
        self.assertIn('g_hc', gridder.ds_gridded)
        self.assertIn('g_phc', gridder.ds_gridded)

    def test_gridded_variables_not_all_nan(self):

        gridder = Gridder(ds_mission=self.test_dataset)
        gridder.create_gridded_dataset()
        skip_vars = ['g_phc']
        vars_to_test = [var for var in gridder.ds_gridded.data_vars if var not in skip_vars]

        # Test each gridded variable
        for var in vars_to_test:
            # print(f"Testing variable: {var}")
            data = gridder.ds_gridded[var].values
            self.assertFalse(np.all(np.isnan(data)), f"Variable {var} contains all NaN values:{data}")
            self.assertTrue(np.any(~np.isnan(data)), f"Variable {var} should contain some valid values:{data}")


if __name__ == '__main__':
    unittest.main()
