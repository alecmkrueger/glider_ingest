import unittest
from datetime import datetime
from glider_ingest.variable import Variable

class TestVariable(unittest.TestCase):
    def test_variable_basic_initialization(self):
        var = Variable(short_name='temperature')
        self.assertIsNone(var.data_source_name)
        self.assertEqual(var.type, 'platform')
        self.assertIsNone(var.id)

    def test_variable_with_data(self):
        var = Variable(
            data_source_name="temperature",
            accuracy=0.1,
            units="celsius",
            id="307"
        )
        self.assertEqual(var.data_source_name, "temperature")
        self.assertEqual(var.accuracy, 0.1)
        self.assertEqual(var.units, "celsius")
        self.assertEqual(var.id, "307")
        self.assertEqual(var.short_name, "temperature")

    def test_post_init_timestamp_generation(self):
        var = Variable(short_name='temperature')
        self.assertIsNotNone(var.update_time)
        # Verify timestamp format
        datetime.strptime(var.update_time, '%Y-%m-%d %H:%M:%S')

    def test_post_init_long_name_generation(self):
        var = Variable(id="307",short_name='temperature')
        self.assertEqual(var.long_name, "Slocum Glider 307")

    def test_to_dict_filtering(self):
        var = Variable(
            data_source_name="temp",
            units="celsius",
            accuracy=None
        )
        result = var.to_dict()
        self.assertNotIn("accuracy", result)
        self.assertEqual(result["data_source_name"], "temp")
        self.assertEqual(result["units"], "celsius")

    def test_variable_with_mixed_types(self):
        var = Variable(short_name='temperature',
            resolution=0.5,
            bytes=32,
            valid_max=25.5,
            valid_min=-5.0
        )
        self.assertIsInstance(var.resolution, float)
        self.assertIsInstance(var.bytes, int)
        self.assertIsInstance(var.valid_max, float)
        self.assertIsInstance(var.valid_min, float)

    def test_short_name_fallback(self):
        var = Variable(data_source_name="pressure")
        self.assertEqual(var.short_name, "pressure")
        
        var2 = Variable(data_source_name="temp", short_name="temperature")
        self.assertEqual(var2.short_name, "temperature")

    def test_to_dict_sorting(self):
        var = Variable(
            units="celsius",
            data_source_name="temp",
            accuracy=0.1
        )
        result = var.to_dict()
        keys = list(result.keys())
        self.assertEqual(keys, sorted(keys))

if __name__ == '__main__':
    unittest.main()
