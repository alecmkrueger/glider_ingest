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

    # Add custom variables to the mission_data container using Variable objects

    # Create the variable by assigning attributes after initialization
    m_water_vx = Variable()  # Initialize the variable
    m_water_vx.data_source_name = 'm_water_vx'  # Variable name in the memory card
    m_water_vx.short_name = 'vx_currents'  # Variable name in the netcdf file
    m_water_vx.long_name = 'x-component of water velocity'
    m_water_vx.units = 'm/s'
    m_water_vx.comment = 'This is a comment'
    
    # Initialize the variable by passing attributes as keyword arguments
    m_water_vy = Variable(data_source_name='m_water_vy', short_name = 'vy_currents',
                          long_name = 'y-component of water velocity',
                          units = 'm/s', comment = 'This is a comment')

    mission_data.add_variables(variables=[m_water_vx,m_water_vy])  # Add the variables as a list of Variable objects
    # Pass the mission_data container to the MissionProcessor class
    # call save_mission_dataset to generate and save the mission dataset
    MissionProcessor(mission_data=mission_data).save_mission_dataset()

if __name__ == '__main__':
    main()
