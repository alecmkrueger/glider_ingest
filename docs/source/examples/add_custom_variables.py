from pathlib import Path

from glider_ingest import MissionData, MissionProcessor, Variable

def main():
    memory_card_copy_loc = Path('path/to/memory/card/copy')
    # Where you want the netcdf to be saved to
    working_dir = Path('path/to/working/dir').resolve()
    mission_num = '46'

    # Initalize the mission_data container
    mission_data = MissionData(memory_card_copy_loc=memory_card_copy_loc,
                            working_dir=working_dir,
                            mission_num=mission_num)

    # Add custom variables to the mission_data container
    m_water_vx = Variable(data_source_name='m_water_vx')  # Initialize the variable
    m_water_vy = Variable(data_source_name='m_water_vy')  # Initialize the variable
    mission_data.add_variables(variables=[m_water_vx,m_water_vy])  # Add the variables as a list of Variable objects
    # Pass the mission_data container to the MissionProcessor class
    # call save_mission_dataset to generate and save the mission dataset
    MissionProcessor(mission_data=mission_data).save_mission_dataset()

if __name__ == '__main__':
    main()
