from pathlib import Path

from glider_ingest import Processor, Variable

def main():
    memory_card_copy_loc = Path('path/to/memory/card/copy')
    # Where you want the netcdf to be saved to
    working_dir = Path('path/to/working/dir').resolve()
    mission_num = '46'

    # Initalize the mission_data container
    processor = Processor(memory_card_copy_loc=memory_card_copy_loc,
                            working_dir=working_dir,
                            mission_num=mission_num)

    # Add custom variables to the mission_data container using strings
    processor.add_mission_vars(variables=['m_water_vx','m_water_vy'])
    processor.process()

if __name__ == '__main__':
    main()
