import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from glider_ingest.MissionProcessor import MissionProcessor
from glider_ingest.MissionData import MissionData
import pytest

class TestMissionProcessor(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(__file__).parent.joinpath("test_data")
        memory_card_copy_loc=Path(self.test_dir).joinpath("memory_card_copy")
        working_dir=Path(self.test_dir).joinpath("working")
        self.mission_data = MissionData(
            memory_card_copy_loc=memory_card_copy_loc,
            working_dir=working_dir,
            mission_num="123",
            glider_id='199'
        )
        self.mission_data.setup()
        
        # Create test time coordinates
        self.time = pd.date_range("2023-01-01", periods=24, freq="h")
        
        # Create test datasets
        self.test_sci_data = xr.Dataset(
            {
                "temperature": (["time"], np.linspace(20, 25, 24)),
                "salinity": (["time"], np.linspace(35, 36, 24)),
                "latitude": (["time"], np.linspace(28.5, 29.0, 24)),
                "longitude": (["time"], np.linspace(-94.5, -94.0, 24)),
                "depth": (["time"], np.linspace(0, 100, 24))
            },
            coords={"time": self.time, "m_time": self.time}
        )
        
        self.test_fli_data = xr.Dataset(
            {
                "pitch": (["time"], np.linspace(-30, 30, 24)),
                "roll": (["time"], np.linspace(-5, 5, 24))
            },
            coords={"time": self.time}
        )
        
        self.mission_data.ds_sci = self.test_sci_data
        self.mission_data.ds_fli = self.test_fli_data
        self.processor = MissionProcessor(mission_data=self.mission_data)

    def test_initialization(self):
        self.assertIsInstance(self.processor.mission_data, MissionData)
        self.assertEqual(self.processor.mission_data.mission_num, "123")
        self.assertEqual(self.processor.mission_data.glider_id, "199")


    def test_add_global_attrs_validation(self):
        self.mission_data.ds_mission = self.test_sci_data
        self.processor.add_global_attrs()
        
        required_attrs = [
            "Conventions",
            "cdm_data_type",
            "featureType",
            "geospatial_bounds_crs",
            "institution",
            "platform_type",
            "wmo_id"
        ]
        
        for attr in required_attrs:
            self.assertIn(attr, self.mission_data.ds_mission.attrs)
        
        self.assertEqual(self.mission_data.ds_mission.attrs["platform_type"], "Slocum Glider")
        self.assertEqual(self.mission_data.ds_mission.attrs["wmo_id"], "unknown")

    def test_save_mission_dataset(self):
        # Setup test dataset
        self.mission_data.ds_mission = self.test_sci_data
        self.mission_data.output_nc_path = self.test_dir / "test_output.nc"
        
        # Test save functionality
        self.processor.save_mission_dataset()
        
        # Verify file creation
        self.assertTrue(self.mission_data.output_nc_path.exists())

    def tearDown(self):
        # Clean up test files
        if hasattr(self.mission_data, 'output_nc_path') and self.mission_data.output_nc_path.exists():
            self.mission_data.output_nc_path.unlink()
            