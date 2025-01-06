import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from unittest.mock import Mock, patch
from glider_ingest.MissionProcessor import MissionProcessor
from glider_ingest.MissionData import MissionData

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
        
        # Create mock dataset
        time = pd.date_range("2023-01-01", periods=24, freq="h")
        lat = np.linspace(28.5, 29.0, 24)
        lon = np.linspace(-94.5, -94.0, 24)
        depth = np.linspace(0, 100, 24)
        
        self.mock_dataset = xr.Dataset(
            {
                "latitude": (["time"], lat),
                "longitude": (["time"], lon),
                "depth": (["time"], depth),
            },
            coords={"time": time, "m_time": time}
        )
        
        self.mission_data.ds_sci = self.mock_dataset
        self.mission_data.ds_fli = self.mock_dataset
        self.processor = MissionProcessor(mission_data=self.mission_data)

    def test_initialization(self):
        self.assertIsInstance(self.processor.mission_data, MissionData)
        self.assertEqual(self.processor.mission_data.mission_num, "123")

    def test_add_global_attrs(self):
        self.mission_data.ds_mission = self.mock_dataset
        self.mission_data.setup()
        self.processor.add_global_attrs()
        
        required_attrs = [
            'Conventions', 'cdm_data_type', 'featureType', 'title',
            'institution', 'source', 'wmo_id'
        ]
        
        for attr in required_attrs:
            self.assertIn(attr, self.mission_data.ds_mission.attrs)
        
        self.assertEqual(self.mission_data.ds_mission.attrs['wmo_id'], 'unknown')
        self.assertEqual(self.mission_data.ds_mission.attrs['featureType'], 'profile')

    @patch('glider_ingest.ScienceProcessor.ScienceProcessor')
    def test_process_sci(self, mock_sci_processor):
        mock_processor = Mock()
        mock_processor.mission_data = self.mission_data
        mock_sci_processor.return_value = mock_processor
        
        result = self.processor.process_sci()
        self.assertEqual(result, self.mission_data)
        mock_processor.process_sci_data.assert_called_once()

    @patch('glider_ingest.FlightProcessor.FlightProcessor')
    def test_process_fli(self, mock_fli_processor):
        mock_processor = Mock()
        mock_processor.mission_data = self.mission_data
        mock_fli_processor.return_value = mock_processor
        
        result = self.processor.process_fli()
        self.assertEqual(result, self.mission_data)
        mock_processor.process_flight_data.assert_called_once()

    def test_generate_mission_dataset(self):
        with patch.object(self.processor, 'process_sci') as mock_sci:
            with patch.object(self.processor, 'process_fli') as mock_fli:
                mock_sci.return_value = self.mission_data
                mock_fli.return_value = self.mission_data
                
                self.processor.generate_mission_dataset()
                
                self.assertIsInstance(self.mission_data.ds_mission, xr.Dataset)
                mock_sci.assert_called_once()
                mock_fli.assert_called_once()

    @patch('xarray.Dataset.to_netcdf')
    def test_save_mission_dataset(self, mock_to_netcdf):
        self.mission_data.ds_mission = self.mock_dataset
        self.mission_data.output_nc_path = self.test_dir / "test_output.nc"
        
        self.processor.save_mission_dataset()
        mock_to_netcdf.assert_called_once_with(
            self.mission_data.output_nc_path,
            engine='netcdf4'
        )

    def test_generate_mission_dataset_data_combination(self):
        self.mission_data.ds_sci = xr.Dataset({"var1": ("time", [1, 2, 3])})
        self.mission_data.ds_fli = xr.Dataset({"var2": ("time", [4, 5, 6])})
        
        with patch.object(self.processor, 'process_sci'):
            with patch.object(self.processor, 'process_fli'):
                self.processor.generate_mission_dataset()
                
                self.assertIn("var1", self.mission_data.ds_mission)
                self.assertIn("var2", self.mission_data.ds_mission)

    def tearDown(self):
        # Clean up any test files if needed
        pass

if __name__ == '__main__':
    unittest.main()
