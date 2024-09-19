from pathlib import Path

from glider_ingest import MissionData, MissionProcessor

memory_card_copy_loc = Path('G:/Shared drives/Slocum Gliders/Mission Data & Files/2024 Missions/Mission 46/Memory card copy/')
working_dir = Path('data').resolve()
mission_num = '46'

mission_data=MissionData(memory_card_copy_loc=memory_card_copy_loc,
                         working_dir=working_dir,
                         mission_num=mission_num)

MissionProcessor(mission_data=mission_data).save_mission_dataset()
