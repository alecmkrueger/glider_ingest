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
    # Then call generate_mission_dataset create the mission dataset
    processor.process()
    # Before we edit the dataset let's get a copy as good practice
    ds = processor.ds.copy(deep=True)
    # Now you can modify ds as needed
    # For example, you can add a new variable
    ds = ds.assign(new_var=('new_var', [1, 2, 3]))
    # Or you can modify an existing variable, say we want to convert temperature from Celsius to Kelvin
    ds['temperature'] = ds['temperature'] + 273.15
    # Then you can save the modified dataset
    ds.to_netcdf(processor.netcdf_output_path)
    
if __name__ == '__main__':
    main()