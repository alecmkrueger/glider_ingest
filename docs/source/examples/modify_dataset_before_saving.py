from pathlib import Path

from glider_ingest import MissionData, MissionProcessor

def main():
    """
    Example of how to use the MissionProcessor and MissionData classes to generate and save a mission dataset
    """    
    memory_card_copy_loc = Path('path/to/memory/card/copy')
    # Where you want the netcdf to be saved to
    working_dir = Path('path/to/working/dir').resolve()
    mission_num = '46'

    # Initalize the mission_data container
    mission_data = MissionData(memory_card_copy_loc=memory_card_copy_loc,
                            working_dir=working_dir,
                            mission_num=mission_num)
    # Pass the mission_data container to the MissionProcessor class
    processor = MissionProcessor(mission_data=mission_data)
    # Then call generate_mission_dataset create the mission dataset
    processor.generate_mission_dataset()
    # Before we edit the dataset let's get a copy
    ds = processor.mission_data.ds_mission.copy(deep=True)
    # Now you can modify ds as needed
    # For example, you can add a new variable
    ds = ds.assign(new_var=('new_var', [1, 2, 3]))
    # Or you can modify an existing variable, say we want to convert temperature from Celsius to Kelvin
    ds['temperature'] = ds['temperature'] + 273.15
    # Then you can save the modified dataset
    ds.to_netcdf(processor.mission_data.mission_dataset_path)
    
if __name__ == '__main__':
    main()