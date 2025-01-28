from pathlib import Path

from glider_ingest import Processor
from glider_ingest.utils import timing

@timing
def main():
    """
    Example of how to use the MissionProcessor and MissionData classes to generate and save a mission dataset
    """    
    memory_card_copy_path = Path('C:/Users/alecmkrueger/Documents/GERG/GERG_GitHub/GERG-Glider/Code/Packages/glider_ingest/src/tests/test_data/memory_card_copy')
    # memory_card_copy_path = Path('G:/Shared drives/Slocum Gliders/Mission Data & Files/2024 Missions/Mission 48/Memory card copy')

    # Where you want the netcdf to be saved to
    working_dir = Path('C:/Users/alecmkrueger/Documents/GERG/GERG_GitHub/GERG-Glider/Code/Packages/glider_ingest/src/tests/test_data/working_dir').resolve()
    mission_num = '48'

    # Init a processor object
    processor = Processor(memory_card_copy_path=memory_card_copy_path,
                            working_dir=working_dir,
                            mission_num=mission_num)
    # Add custom variables to the mission_data container as a list of strings
    processor.add_mission_vars(mission_vars=['m_water_vy','m_water_vx'])
    # Save the container to a netcdf file
    processor.save()
    
    
if __name__ == '__main__':
    main()
