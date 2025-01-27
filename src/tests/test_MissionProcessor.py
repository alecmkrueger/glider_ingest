import unittest
from pathlib import Path
import xarray as xr
import numpy as np
import pandas as pd
from glider_ingest import MissionProcessor, MissionData

class TestMissionProcessor(unittest.TestCase):
    def setUp(self):
        # Create test paths
        self.test_dir = Path(__file__).parent
        self.memory_card_copy_loc = self.test_dir.joinpath('test_data/memory_card_copy')
        self.working_dir = self.test_dir.joinpath('test_data/working_dir').resolve()
        self.mission_num = '46'
        
        # Create base MissionData instance
        self.mission_data = MissionData(
            memory_card_copy_loc=self.memory_card_copy_loc,
            working_dir=self.working_dir,
            mission_num=self.mission_num
        )

    def test_generate_mission_dataset(self):
        processor = MissionProcessor(mission_data=self.mission_data)
        processor.generate_mission_dataset()
        
        self.assertTrue(hasattr(processor.mission_data, 'ds_mission'))
        self.assertIn('temperature', processor.mission_data.ds_mission)
        self.assertIn('pressure', processor.mission_data.ds_mission)

    def test_save_mission_dataset(self):
        processor = MissionProcessor(mission_data=self.mission_data)
        self.mission_data.output_nc_path = self.working_dir / 'test_output.nc'
        
        processor.save_mission_dataset()
        self.assertTrue(self.mission_data.output_nc_path.exists())
