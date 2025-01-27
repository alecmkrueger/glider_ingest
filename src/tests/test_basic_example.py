import unittest
from pathlib import Path
from glider_ingest import MissionData, MissionProcessor

import pytest

@pytest.mark.slow()
class TestBasicExample(unittest.TestCase):
    def setUp(self):
        tests_path = Path(__file__).parent
        self.memory_card_copy_loc = tests_path.joinpath('test_data/memory_card_copy')
        self.working_dir = tests_path.joinpath('test_data/working_dir').resolve()
        self.mission_num = '46'
        
    def test_mission_processing(self):
        # Test MissionData initialization
        mission_data = MissionData(
            memory_card_copy_loc=self.memory_card_copy_loc,
            working_dir=self.working_dir,
            mission_num=self.mission_num
        )
        self.assertIsInstance(mission_data, MissionData)
        
        # Test MissionProcessor
        processor = MissionProcessor(mission_data=mission_data)
        self.assertIsInstance(processor, MissionProcessor)
        
        # Test dataset generation and saving
        processor.save_mission_dataset()
        self.assertTrue(hasattr(processor.mission_data, 'ds_mission'))
        
        # Test dataset contents
        ds = processor.mission_data.ds_mission
        self.assertIsNotNone(ds)
        self.assertTrue(len(list(ds.keys())) > 0)

if __name__ == '__main__':
    unittest.main()