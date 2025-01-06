import unittest
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
import pytest
from datetime import datetime, timedelta
from glider_ingest.ScienceProcessor import ScienceProcessor
from glider_ingest.MissionData import MissionData

class TestScienceProcessor(unittest.TestCase):
    def setUp(self):
        # Create mock MissionData instance
        self.mission_data = MissionData(
            memory_card_copy_loc=Path("test_data/memory_card_copy"),
            working_dir=Path("test_data/working"),
            glider_id="307",
            mission_num="45",
            mission_start_date=datetime(2024, 1, 1),
            mission_end_date=datetime(2024, 1, 2)
        )
        
        # Create sample science DataFrame
        times = pd.date_range('2024-01-01', periods=24, freq='h')
        self.test_df = pd.DataFrame({
            'sci_m_present_time': times,
            'sci_water_pressure': np.random.uniform(0, 100, 24),
            'sci_water_temp': np.random.uniform(20, 25, 24),
            'sci_water_cond': np.random.uniform(3, 4, 24),
            'sci_oxy4_oxygen': np.random.uniform(180, 220, 24),
            'sci_flbbcd_bb_units': np.random.uniform(0, 1, 24),
            'sci_flbbcd_cdom_units': np.random.uniform(0, 50, 24),
            'sci_flbbcd_chlor_units': np.random.uniform(0, 10, 24),
            'sci_water_sal':np.random.uniform(0, 10, 24),
            'sci_water_dens':np.random.uniform(0, 10, 24)
        })
        
        self.processor = ScienceProcessor(self.mission_data)
        self.processor.mission_data.df_sci = self.test_df

    def test_get_sci_vars_all_sensors(self):
        variables = ['sci_oxy4_oxygen', 'sci_flbbcd_bb_units', 'sci_water_pressure']
        result = self.processor.get_sci_vars(variables)
        self.assertIn('sci_water_pressure', result)
        self.assertIn('sci_oxy4_oxygen', result)
        self.assertIn('sci_flbbcd_bb_units', result)

    def test_get_sci_vars_no_optical(self):
        variables = ['sci_oxy4_oxygen', 'sci_water_pressure']
        result = self.processor.get_sci_vars(variables)
        self.assertIn('sci_water_pressure', result)
        self.assertIn('sci_oxy4_oxygen', result)
        self.assertNotIn('sci_flbbcd_bb_units', result)

    def test_get_sci_vars_no_oxygen(self):
        variables = ['sci_flbbcd_bb_units', 'sci_water_pressure']
        result = self.processor.get_sci_vars(variables)
        self.assertIn('sci_water_pressure', result)
        self.assertIn('sci_flbbcd_bb_units', result)
        self.assertNotIn('sci_oxy4_oxygen', result)

    def test_get_sci_vars_no_oxygen_and_optical(self):
        variables = ['sci_water_pressure']
        result = self.processor.get_sci_vars(variables)
        self.assertIn('sci_water_pressure', result)
        self.assertNotIn('sci_flbbcd_bb_units', result)
        self.assertNotIn('sci_oxy4_oxygen', result)

    def test_convert_sci_df_to_ds(self):
        self.processor.convert_sci_df_to_ds()
        self.assertIsInstance(self.processor.mission_data.ds_sci, xr.Dataset)
        self.assertEqual(self.processor.mission_data.ds_sci.platform.values, "307")

    def test_add_sci_attrs(self):
        self.processor.convert_sci_df_to_ds()
        self.processor.add_sci_attrs()
        
        # Check platform attributes
        self.assertIn('platform', self.processor.mission_data.ds_sci)
        self.assertIn('wmo_id', self.processor.mission_data.ds_sci.platform.attrs)
        
        # Check variable attributes
        self.assertIn('units', self.processor.mission_data.ds_sci.sci_water_temp.attrs)
        self.assertIn('standard_name', self.processor.mission_data.ds_sci.sci_water_pressure.attrs)

    def test_format_sci_ds(self):
        self.processor.convert_sci_df_to_ds()
        self.processor.format_sci_ds()
        
        # Check renamed variables
        self.assertIn('time', self.processor.mission_data.ds_sci.dims)
        self.assertIn('pressure', self.processor.mission_data.ds_sci)
        self.assertIn('temperature', self.processor.mission_data.ds_sci)

    @pytest.mark.slow
    def test_process_sci_data_full_workflow(self):
        # Run the full processing workflow
        self.processor.process_sci_data()
        
        # Verify final dataset structure
        self.assertIsInstance(self.processor.mission_data.ds_sci, xr.Dataset)
        self.assertIn('pressure', self.processor.mission_data.ds_sci)
        self.assertIn('temperature', self.processor.mission_data.ds_sci)
        self.assertIn('platform', self.processor.mission_data.ds_sci)


