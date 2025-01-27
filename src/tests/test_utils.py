import unittest
import numpy as np
import xarray as xr
from glider_ingest.utils import (
    print_time, find_nth, invert_dict, 
    get_polygon_coords,
    timing,get_wmo_id, f_print
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
        import io
        import sys
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


