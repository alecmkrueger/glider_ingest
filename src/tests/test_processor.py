import unittest
from pathlib import Path
import pandas as pd
from glider_ingest.processor import Processor
from glider_ingest.variable import Variable

class TestProcessor(unittest.TestCase):
    def setUp(self):
        self.memory_card_copy_path = Path('test_data/memory_card_copy')
        self.working_dir = Path('test_data/working_dir')
        self.processor = Processor(
            memory_card_copy_path=self.memory_card_copy_path,
            working_dir=self.working_dir,
            mission_num='46'
        )

    def test_copy_files_filters_correctly(self):
        # Create test directory structure
        test_source = self.memory_card_copy_path / 'Flight_card'
        test_source.mkdir(parents=True,exist_ok=True)
        (test_source / 'LOGS').mkdir(exist_ok=True)
        (test_source / 'STATE' / 'CACHE').mkdir(parents=True,exist_ok=True)
        (test_source / 'OTHER').mkdir(exist_ok=True)

        self.processor._copy_files()

        # Verify only LOGS and STATE/CACHE were copied
        dest_path = self.working_dir / self.processor.mission_folder_name / 'Flight_card'
        self.assertTrue((dest_path / 'LOGS').exists())
        self.assertTrue((dest_path / 'STATE' / 'CACHE').exists())
        self.assertFalse((dest_path / 'OTHER').exists())

    def test_get_mission_variables(self):
        test_vars = [Variable(data_source_name='test1'), Variable(data_source_name='test2')]
        self.processor.mission_vars = test_vars
        
        variables = self.processor._get_mission_variables()
        self.assertEqual(len(variables), 2)
        self.assertEqual(variables[0].data_source_name, 'test1')

    def test_format_time(self):
        test_df = pd.DataFrame({
            'time': [1577836800, 1577923200],  # 2020-01-01, 2020-01-02
            'value': [1, 2]
        })
        
        formatted_df = self.processor._format_time(test_df)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(formatted_df['time']))
        self.assertEqual(len(formatted_df), 2)

    def test_update_dataframe_columns(self):
        test_var = Variable(data_source_name='test_source', short_name='test_short')
        self.processor.mission_vars = [test_var]
        
        test_df = pd.DataFrame({'test_source': [1, 2, 3]})
        updated_df = self.processor._update_dataframe_columns(test_df)
        
        self.assertIn('test_short', updated_df.columns)
        self.assertNotIn('test_source', updated_df.columns)

if __name__ == '__main__':
    unittest.main()
