import unittest
import numpy as np
import xarray as xr
import datetime
from glider_ingest.utils import (
    print_time, find_nth, invert_dict, 
    add_gridded_data, get_polygon_coords
)

class TestUtils(unittest.TestCase):
    def setUp(self):
        # Create sample dataset for testing
        times = np.array(['2023-01-01T00:00:00', '2023-01-01T01:00:00'], dtype='datetime64[ns]')
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

    def test_add_gridded_data(self):
        result_ds = add_gridded_data(self.test_ds)
        
        # Check if gridded variables were added
        self.assertIn('g_temp', result_ds)
        self.assertIn('g_salt', result_ds)
        self.assertIn('g_depth', result_ds)
        
        # Verify dimensions
        self.assertIn('g_time', result_ds.g_temp.dims)
        self.assertIn('g_pres', result_ds.g_temp.dims)

    def test_get_polygon_coords(self):
        polygon = get_polygon_coords(self.test_ds)
        
        # Check polygon string format
        self.assertTrue(polygon.startswith('POLYGON (('))
        self.assertTrue(polygon.endswith('))'))
        
        # Verify coordinate count (5 points for closed polygon)
        coord_pairs = polygon.count(' ') // 2  # Each coordinate pair has lat lon
        self.assertEqual(coord_pairs, 5)

    def test_get_polygon_coords_single_point(self):
        # Test with dataset containing single point
        single_ds = self.test_ds.isel(time=[0])
        polygon = get_polygon_coords(single_ds)
        self.assertIsInstance(polygon, str)
        self.assertTrue(polygon.startswith('POLYGON (('))

    def test_find_nth_empty_string(self):
        self.assertEqual(find_nth("", ".", 1), -1)
        self.assertEqual(find_nth("", ".", 0), -1)

    def test_invert_dict_duplicate_values(self):
        test_dict = {"a": 1, "b": 1, "c": 2}
        inverted = invert_dict(test_dict)
        self.assertEqual(len(inverted), 2)  # Only unique values become keys

if __name__ == '__main__':
    unittest.main()
