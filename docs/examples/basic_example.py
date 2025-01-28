from pathlib import Path

from glider_ingest import Processor

def main():
    """
    Example of how to use the MissionProcessor and MissionData classes to generate and save a mission dataset
    """    
    memory_card_copy_path = Path('path/to/memory/card/copy')
    # Where you want the netcdf to be saved to
    working_dir = Path('path/to/working/dir').resolve()
    mission_num = '46'

    # Init a processor object
    processor = Processor(memory_card_copy_path=memory_card_copy_path,
                          working_dir=working_dir,
                          mission_num=mission_num)
    # Save to a netcdf file
    processor.save()
    
    
if __name__ == '__main__':
    main()
