import unittest
from pathlib import Path
import datetime
import tempfile
import os
from glider_ingest.MissionData import MissionData

class TestMissionData(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(__file__).parent.joinpath("test_data")
        self.memory_card_copy_loc=Path(self.test_dir).joinpath("memory_card_copy")
        self.working_dir=Path(self.test_dir).joinpath("working")
        self.mission_data = MissionData(
            memory_card_copy_loc=self.memory_card_copy_loc,
            working_dir=self.working_dir,
            mission_num="45"
        )

    def create_test_sci_file(self):
        sci_path = Path(self.test_dir) / "Science_card/logs"
        sci_path.mkdir(parents=True)
        test_file = sci_path / "test.ebd"
        test_file.write_text("full_filename: unit_307-2024-test")
        return sci_path

    def test_initialization(self):
        self.assertIsInstance(self.mission_data.memory_card_copy_loc, Path)
        self.assertIsInstance(self.mission_data.working_dir, Path)
        self.assertEqual(self.mission_data.mission_num, "45")

    def test_get_file_locs(self):
        self.mission_data.get_file_locs()
        self.assertEqual(self.mission_data.fli_files_loc.name, "logs")
        self.assertEqual(self.mission_data.sci_files_loc.name, "logs")
        self.assertIn("Flight_card", str(self.mission_data.fli_cache_loc))
        self.assertIn("Science_card", str(self.mission_data.sci_cache_loc))

    def test_get_mission_date_range_default(self):
        self.mission_data.get_mission_date_range()
        self.assertEqual(self.mission_data.mission_start_date, "2010-01-01")
        tomorrow_plus_year = (datetime.datetime.today() + datetime.timedelta(days=365)).date()
        self.assertEqual(self.mission_data.mission_end_date, str(tomorrow_plus_year))

    def test_get_mission_date_range_custom(self):
        mission = MissionData(
            memory_card_copy_loc=Path(self.test_dir),
            working_dir=Path(self.test_dir),
            mission_num="45",
            mission_start_date="2024-01-01",
            mission_end_date="2024-12-31"
        )
        mission.get_mission_date_range()
        self.assertEqual(mission.mission_start_date, "2024-01-01")
        self.assertEqual(mission.mission_end_date, "2024-12-31")
        
    def test_get_mission_year_and_glider_with_glider_name(self):
        self.mission_data.glider_name = "Reveille"
        self.mission_data.setup()
        self.mission_data.get_mission_year_and_glider()
        self.assertEqual(self.mission_data.mission_year, "2024")
        self.assertEqual(self.mission_data.glider_id, "307")
    
    def test_extract_full_filename_missing_full_filename(self):
        file = self.test_dir.joinpath("working/test.ebd")
        file.write_text("unit_307-2024-test")
        full_filename = self.mission_data._extract_full_filename(file)
        self.assertIsNone(full_filename)
        if file.exists():
            file.unlink()

    def test_get_wmo_id(self):
        self.mission_data.glider_id = "307"
        self.mission_data.get_wmo_id()
        self.assertEqual(self.mission_data.wmo_id, "4801938")

    def test_get_mission_title_default(self):
        self.mission_data.get_mission_title()
        self.assertEqual(self.mission_data.mission_title, "Mission 45")

    def test_get_mission_title_custom(self):
        mission = MissionData(
            memory_card_copy_loc=Path(self.test_dir),
            working_dir=Path(self.test_dir),
            mission_num="45",
            mission_title="Custom Mission"
        )
        mission.get_mission_title()
        self.assertEqual(mission.mission_title, "Custom Mission")

    def test_get_nc_filename(self):
        self.mission_data.glider_id = "307"
        self.mission_data.mission_year = "2024"
        self.mission_data.get_nc_filename()
        self.assertEqual(self.mission_data.nc_filename, "M45_2024_307.nc")

    def test_get_files_missing_directory(self):
        with self.assertRaises(ValueError):
            self.mission_data.get_files(Path("nonexistent"), "ebd")

    def test_get_files_no_matching_files(self):
        empty_dir = Path(self.test_dir) / "empty"
        empty_dir.mkdir(exist_ok=True)
        with self.assertRaises(ValueError):
            self.mission_data.get_files(empty_dir, "ebd")

    def test_get_output_nc_path(self):
        # self.mission_data.output_nc_path = Path(self.test_dir).joinpath("output")
        self.mission_data.nc_filename = "test.nc"
        self.mission_data.mission_title = "Test Mission"
        self.mission_data.get_output_nc_path()
        self.assertEqual(self.mission_data.output_nc_path.name, "test.nc")
        self.assertIn("Test Mission", str(self.mission_data.output_nc_path))

