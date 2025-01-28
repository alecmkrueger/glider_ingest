import unittest
import numpy as np
import xarray as xr
import io
import sys
import pytest
from glider_ingest.utils import (
    print_time, find_nth, invert_dict, 
    get_polygon_coords,
    timing,get_wmo_id, f_print, get_polygon_bounds
)

class TestUtils(unittest.TestCase):
    def setUp(self):
        # Create sample dataset for testing
        times = np.array(['2024-01-01T00:00:00', '2024-01-01T01:00:00'], dtype='datetime64[ns]')
        self.test_ds = xr.Dataset(
            data_vars={
                'pressure': ('time', [0, 10]),
                'temperature': ('time', [20, 21]),
                'salinity': ('time', [35, 35.5]),
                'conductivity': ('time', [3.5, 3.6]),
                'density': ('time', [1020, 1021]),
                'oxygen': ('time', [200, 205]),
                'latitude': ('time', [28.5, 28.6]),
                'longitude': ('time', [-80.0, -80.1])
            },
            coords={'time': times}
        )
        vars_to_grid = ['temperature', 'salinity', 'conductivity', 'density', 'oxygen']
        for var in vars_to_grid:
            self.test_ds[var].attrs['to_grid'] = True


    def test_print_time(self):
        test_message = "Test Message"
        # Capture print output
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        print_time(test_message)
        sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue().strip()
        self.assertIn(test_message, output)
        self.assertIn(":", output)
            
    def test_f_print(self):
        # Test variables
        x = 42
        y = "test"
        z = [1, 2, 3]
        
        # Test return_string=True
        result = f_print(x, y, z, return_string=True)
        self.assertIn("x = 42", result)
        self.assertIn("y = test", result)
        self.assertIn("z = [1, 2, 3]", result)
        
        # Test print output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        f_print(x, y, z)
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue().strip()
        
        self.assertIn("x = 42", output)
        self.assertIn("y = test", output)
        self.assertIn("z = [1, 2, 3]", output)
        
        # Test value with no variable assignment
        result = f_print(1, return_string=True)
        self.assertIn("Could not determine variable name for value: 1", result)


    def test_find_nth(self):
        test_string = "test.string.with.dots"
        self.assertEqual(find_nth(test_string, ".", 1), 4)
        self.assertEqual(find_nth(test_string, ".", 2), 11)
        self.assertEqual(find_nth(test_string, ".", 3), 16)
        self.assertEqual(find_nth(test_string, ".", 4), -1)
        self.assertEqual(find_nth("no_dots", ".", 1), -1)

    def test_invert_dict(self):
        test_dict = {"a": 1, "b": 2, "c": 3}
        inverted = invert_dict(test_dict)
        self.assertEqual(inverted[1], "a")
        self.assertEqual(inverted[2], "b")
        self.assertEqual(inverted[3], "c")
        
        # Test empty dict
        self.assertEqual(invert_dict({}), {})

    def test_get_polygon_bounds(self):
        # Test data
        longitude = np.array([-80.0, -80.1, -80.2])
        latitude = np.array([28.5, 29.0, 29.4])
        
        bounds = get_polygon_bounds(longitude, latitude)
        self.assertEqual(len(bounds), 4)
        self.assertLess(bounds[0], 29.5)  # lat_max
        self.assertGreater(bounds[0], bounds[1])  # lat_max > lat_min
        self.assertGreater(bounds[2], bounds[3])  # lon_max > lon_min

    def test_get_polygon_coords(self):
        # Test data
        longitude = np.array([-80.0, -80.1, -80.2])
        latitude = np.array([28.5, 29.0, 29.4])
        lat_max, lat_min = 29.4, 28.5
        lon_max, lon_min = -80.0, -80.2
        
        polygon = get_polygon_coords(longitude, latitude, lat_max, lat_min, lon_max, lon_min)
        
        # Check polygon string format
        self.assertTrue(polygon.startswith('POLYGON (('))
        self.assertTrue(polygon.endswith('))'))
        
        # Verify coordinate count (5 points for closed polygon)
        coord_pairs = polygon.count(',') + 1  # Number of coordinate pairs
        self.assertEqual(coord_pairs, 5)

    def test_get_polygon_bounds_edge_cases(self):
        # Test with all latitudes above 29.5
        longitude = np.array([-80.0, -80.1])
        latitude = np.array([30.0, 30.1])
        
        with self.assertRaises(ValueError):
            get_polygon_bounds(longitude, latitude)
            
        # Test with NaN values
        longitude = np.array([-80.0, np.nan, -80.2])
        latitude = np.array([28.5, 29.0, np.nan])
        bounds = get_polygon_bounds(longitude, latitude)
        self.assertFalse(np.any(np.isnan(bounds)))

    def test_get_wmo_id_additional(self):
        # Test invalid input
        with self.assertRaises(KeyError):
            get_wmo_id('999')
            
        # Test different input types
        self.assertEqual(get_wmo_id(308), '4801915')
        self.assertEqual(get_wmo_id('540'), '4801916')


    def test_find_nth_empty_string(self):
        self.assertEqual(find_nth("", ".", 1), -1)
        self.assertEqual(find_nth("", ".", 0), -1)

    def test_invert_dict_duplicate_values(self):
        test_dict = {"a": 1, "b": 1, "c": 2}
        inverted = invert_dict(test_dict)
        self.assertEqual(len(inverted), 2)  # Only unique values become keys

    def test_timing_decorator(self):
        import io
        import sys
        
        # Create a test function with the timing decorator
        @timing
        def test_func(x):
            return x * 2
        
        # Capture print output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # Run the decorated function
        result = test_func(5)
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        # Verify function execution
        self.assertEqual(result, 10)
        # Verify timing output format
        self.assertIn('func:', output)
        self.assertIn('took:', output)
        self.assertIn('sec', output)

    def test_get_wmo_id(self):
        # Test string input
        self.assertEqual(get_wmo_id('307'), '4801938')
        self.assertEqual(get_wmo_id('308'), '4801915')
        self.assertEqual(get_wmo_id('540'), '4801916')
        
        # Test integer input
        self.assertEqual(get_wmo_id(541), '4801924')
        
        # Test unknown glider
        self.assertEqual(get_wmo_id('199'), 'unknown')
        
        # Test unit glider
        self.assertEqual(get_wmo_id('1148'), '4801915')


