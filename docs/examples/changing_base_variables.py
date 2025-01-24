from pathlib import Path

from glider_ingest import MissionData, MissionProcessor, Variable

def main():
    memory_card_copy_loc = Path('path/to/memory/card/copy')
    # Where you want the netcdf to be saved to
    working_dir = Path('path/to/working/dir')
    mission_num = '46'

    # Initalize the mission_data container
    mission_data = MissionData(memory_card_copy_loc=memory_card_copy_loc,
                            working_dir=working_dir,
                            mission_num=mission_num)
    # Rename the latitude and longitude short names to be 'lat' and 'lon'
    mission_data.mission_vars['m_lat'].short_name = 'lat'
    mission_data.mission_vars['m_lon'].short_name = 'lon'
    # Add custom variables to the mission_data container using strings
    mission_data.add_variables(variables=['m_water_vx','m_water_vy'])
    # Pass the mission_data container to the MissionProcessor class
    # call save_mission_dataset to generate and save the mission dataset
    MissionProcessor(mission_data=mission_data).save_mission_dataset()

if __name__ == '__main__':
    main()
