import unittest
from pathlib import Path
import pandas as pd
import pytest
import shutil
import io
import sys
from glider_ingest.processor import Processor
from glider_ingest.variable import Variable

class TestProcessor(unittest.TestCase):
    def setUp(self):
        self.memory_card_copy_path = Path('test_data/memory_card_copy')
        self.working_dir = Path('test_data/working_dir')
        self.processor = Processor(
            memory_card_copy_path=self.memory_card_copy_path,
            working_dir=self.working_dir,
            mission_num='46',
        )
        
    def test_glider_name(self):
        processor = Processor(
            memory_card_copy_path=self.memory_card_copy_path,
            working_dir=self.working_dir,
            mission_num='46',
            glider_id='307'
        )
        self.assertEqual(processor.glider_name,'Reveille',processor.glider_name)
        
    def test_check_mission_var_duplicates(self):
        # Create a list of variables with duplicate short names
        vars = [
            Variable(short_name='temp', long_name='Temperature'),
            Variable(short_name='temp', long_name='Temperature')]
        
        self.processor.add_mission_vars(vars)
        
    def test_add_mission_vars_all_str(self):
        # Test adding mission variables with all strings
        self.processor.add_mission_vars(['temp', 'salinity', 'pressure'])
        self.assertTrue(all([isinstance(var, Variable) for var in self.processor.mission_vars]))

    def test_copy_cache_files_new_directory_creation_and_copy(self):
        # Setup source cache files
        cache_source = self.memory_card_copy_path / 'Flight_card' / 'STATE' / 'CACHE'
        cache_source.mkdir(parents=True, exist_ok=True)
        
        # Create a test file with content
        test_file = cache_source / 'test_cache.dat'
        test_content = 'test cache content'
        with open(test_file, 'w') as f:
            f.write(test_content)

        # Delete destination directory if it exists
        dest_path = self.working_dir / self.processor.mission_folder_name / 'Flight_card' / 'STATE' / 'CACHE'
        if dest_path.exists():
            shutil.rmtree(dest_path)

        # Capture print output
        with io.StringIO() as captured_output:
            sys.stdout = captured_output
            self.processor._copy_cache_files()
            sys.stdout = sys.__stdout__
            output = captured_output.getvalue()

        # Verify directory was created
        self.assertTrue(dest_path.exists())
        
        # Verify file was copied with correct content
        copied_file = dest_path / 'test_cache.dat'
        self.assertTrue(copied_file.exists())
        with open(copied_file, 'r') as f:
            copied_content = f.read()
        self.assertEqual(copied_content, test_content)
        
        # Verify print message
        self.assertIn(f'Coping {test_file} to {dest_path}', output)


    def test_copy_cache_files_creates_directory(self):
        # Setup test cache files in source
        cache_source = self.memory_card_copy_path / 'Flight_card' / 'STATE' / 'CACHE'
        cache_source.mkdir(parents=True, exist_ok=True)
        test_file = cache_source / 'test_cache.txt'
        test_file.touch()

        # Run copy operation
        self.processor._copy_cache_files()

        # Verify destination directory was created
        dest_path = self.working_dir / self.processor.mission_folder_name / 'Flight_card' / 'STATE' / 'CACHE'
        self.assertTrue(dest_path.exists())
        self.assertTrue(dest_path.is_dir())

    def test_copy_cache_files_copies_files(self):
        # Setup multiple test cache files
        cache_source = self.memory_card_copy_path / 'Flight_card' / 'STATE' / 'CACHE'
        cache_source.mkdir(parents=True, exist_ok=True)
        test_files = ['cache1.txt', 'cache2.dat', 'cache3.bin']
        for file in test_files:
            (cache_source / file).touch()

        # Run copy operation
        self.processor._copy_cache_files()

        # Verify all files were copied
        dest_path = self.working_dir / self.processor.mission_folder_name / 'Flight_card' / 'STATE' / 'CACHE'
        for file in test_files:
            self.assertTrue((dest_path / file).exists())

    def test_copy_cache_files_skip_existing(self):
        # Setup source and destination with existing file
        cache_source = self.memory_card_copy_path / 'Flight_card' / 'STATE' / 'CACHE'
        cache_source.mkdir(parents=True, exist_ok=True)
        dest_path = self.working_dir / self.processor.mission_folder_name / 'Flight_card' / 'STATE' / 'CACHE'
        dest_path.mkdir(parents=True, exist_ok=True)

        # Create test file in both locations
        test_file = 'existing_cache.txt'
        (cache_source / test_file).touch()
        (dest_path / test_file).touch()

        # Modify destination file to be different
        with open(dest_path / test_file, 'w') as f:
            f.write('existing content')

        # Run copy operation
        self.processor._copy_cache_files()

        # Verify existing file wasn't overwritten
        with open(dest_path / test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'existing content')

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
