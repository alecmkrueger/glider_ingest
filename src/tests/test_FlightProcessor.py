import unittest
import pandas as pd
import xarray as xr
from pathlib import Path
from glider_ingest.FlightProcessor import FlightProcessor
from glider_ingest.MissionData import MissionData

import pytest

class TestFlightProcessor(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(__file__).parent.joinpath("test_data")
        memory_card_copy_loc=Path(self.test_dir).joinpath("memory_card_copy")
        working_dir=Path(self.test_dir).joinpath("working")
        self.mission_data = MissionData(
            memory_card_copy_loc=memory_card_copy_loc,
            working_dir=working_dir,
            mission_num="45",
            mission_start_date="2024-01-01",
            mission_end_date="2024-12-31"
        )
        self.flight_processor = FlightProcessor(mission_data=self.mission_data)
        self.sample_flight_df = pd.DataFrame({
            'm_present_time': pd.date_range('2024-01-01', periods=3),
            'm_lat': [25.1, 25.2, 25.3],
            'm_lon': [-94.1, -94.2, -94.3],
            'm_pressure': [10.0, 20.0, 30.0],
            'm_water_depth': [100.0, 200.0, 300.0]
        })

    def test_convert_fli_df_to_ds(self):
        self.flight_processor.mission_data.df_fli = self.sample_flight_df
        self.flight_processor.convert_fli_df_to_ds()
        self.assertIsInstance(self.flight_processor.mission_data.ds_fli, xr.Dataset)
        self.assertIn('m_pressure', self.flight_processor.mission_data.ds_fli.variables)

    def test_format_flight_ds(self):
        test_times = pd.date_range('2024-01-01', periods=3)
        test_ds = xr.Dataset({
            'm_present_time': ('index', test_times),
            'm_pressure': ('index', [10.0, 20.0, 30.0]),
            'm_water_depth': ('index', [100.0, 200.0, 300.0]),
            'm_latitude': ('index', [25.1, 25.2, 25.3]),
            'm_longitude': ('index', [-94.1, -94.2, -94.3])
        })
        self.flight_processor.mission_data.ds_fli = test_ds
        self.flight_processor.format_flight_ds()
        
        self.assertIn('m_time', self.flight_processor.mission_data.ds_fli.dims)
        self.assertIn('depth', self.flight_processor.mission_data.ds_fli.variables)
        self.assertIn('latitude', self.flight_processor.mission_data.ds_fli.variables)
        self.assertIn('longitude', self.flight_processor.mission_data.ds_fli.variables)

    def test_add_flight_attrs(self):
        test_ds = xr.Dataset({
            'm_pressure': ('time', [10.0, 20.0]),
            'm_water_depth': ('time', [100.0, 200.0]),
            'm_latitude': ('time', [25.1, 25.2]),
            'm_longitude': ('time', [-94.1, -94.2])
        })
        self.flight_processor.mission_data.ds_fli = test_ds
        self.flight_processor.add_flight_attrs()
        
        self.assertIn('units', self.flight_processor.mission_data.ds_fli.m_pressure.attrs)
        self.assertIn('standard_name', self.flight_processor.mission_data.ds_fli.m_latitude.attrs)
        self.assertIn('axis', self.flight_processor.mission_data.ds_fli.m_longitude.attrs)
        self.assertIn('update_time', self.flight_processor.mission_data.ds_fli.m_water_depth.attrs)

    @pytest.mark.slow()
    def test_process_flight_data_workflow(self):
        self.flight_processor.mission_data.df_fli = self.sample_flight_df
        self.flight_processor.process_flight_data()
        
        self.assertTrue(hasattr(self.flight_processor.mission_data, 'ds_fli'))
        self.assertIsInstance(self.flight_processor.mission_data.ds_fli, xr.Dataset)
        self.assertIn('latitude', self.flight_processor.mission_data.ds_fli.variables)
        self.assertIn('longitude', self.flight_processor.mission_data.ds_fli.variables)
        self.assertIn('depth', self.flight_processor.mission_data.ds_fli.variables)

