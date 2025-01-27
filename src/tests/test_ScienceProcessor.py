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
        self.test_dir = Path(__file__).parent.joinpath("test_data")
        memory_card_copy_loc=Path(self.test_dir).joinpath("memory_card_copy")
        working_dir=Path(self.test_dir).joinpath("working")
        self.mission_data = MissionData(
            memory_card_copy_loc=memory_card_copy_loc,
            working_dir=working_dir,
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


    def test_filter_sci_vars_missing_vars(self):
        self.processor.filter_sci_vars([''])

    def test_convert_sci_df_to_ds(self):
        self.processor.convert_sci_df_to_ds()
        self.assertIsInstance(self.processor.mission_data.ds_sci, xr.Dataset)
        self.assertEqual(self.processor.mission_data.ds_sci.platform.values, "307")

    @pytest.mark.slow
    def test_process_sci_data_full_workflow(self):
        # Run the full processing workflow
        self.processor.process_sci_data()
        
        # Verify final dataset structure
        self.assertIsInstance(self.processor.mission_data.ds_sci, xr.Dataset)
        self.assertIn('sci_water_pressure', list(self.processor.mission_data.ds_sci.keys()))
        self.assertIn('sci_water_temp', list(self.processor.mission_data.ds_sci.keys()))
        self.assertIn('platform', list(self.processor.mission_data.ds_sci.keys()))


