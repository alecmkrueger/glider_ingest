from pathlib import Path

from glider_ingest import MissionData, MissionProcessor

def main():
    """
    Example of how to use the MissionProcessor and MissionData classes to generate and save a mission dataset
    """    
    # memory_card_copy_loc = Path('C:/Users/alecmkrueger/Documents/GERG/GERG_GitHub/GERG-Glider/Code/Packages/glider_ingest/src/tests/test_data/memory_card_copy')
    memory_card_copy_loc = Path('G:/Shared drives/Slocum Gliders/Mission Data & Files/2024 Missions/Mission 48/Memory card copy')

    # Where you want the netcdf to be saved to
    working_dir = Path('C:/Users/alecmkrueger/Documents/GERG/GERG_GitHub/GERG-Glider/Code/Packages/glider_ingest/src/tests/test_data/working_dir').resolve()
    mission_num = '48'

    # Initalize the mission_data container
    mission_data = MissionData(memory_card_copy_loc=memory_card_copy_loc,
                            working_dir=working_dir,
                            mission_num=mission_num)
    # Add custom variables to the mission_data container as a list of strings
    mission_data.add_variables(variables=['m_water_vy','m_water_vx'])
    # Pass the mission_data container to the MissionProcessor class
    # call save_mission_dataset to generate and save the mission dataset
    MissionProcessor(mission_data=mission_data).save_mission_dataset()
    
    
if __name__ == '__main__':
    main()
