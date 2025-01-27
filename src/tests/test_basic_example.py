from pathlib import Path

from glider_ingest import MissionData, MissionProcessor

from gerg_plotting import ScatterPlot,data_from_ds

def main():
    """
    Example of how to use the MissionProcessor and MissionData classes to generate and save a mission dataset
    """    
    memory_card_copy_loc = Path('test_data/memory_card_copy')
    # Where you want the netcdf to be saved to
    working_dir = Path('test_data/working_dir').resolve()
    mission_num = '46'

    # Initalize the mission_data container
    mission_data = MissionData(memory_card_copy_loc=memory_card_copy_loc,
                            working_dir=working_dir,
                            mission_num=mission_num)
    # Pass the mission_data container to the MissionProcessor class
    # call save_mission_dataset to generate and save the mission dataset
    processor = MissionProcessor(mission_data=mission_data)
    processor.save_mission_dataset()
    # Print the mission dataset
    print(f"Mission Dataset:{list(processor.mission_data.ds_mission.keys())}")
    ds = processor.mission_data.ds_mission

    data = data_from_ds(ds)
    print(data.get_vars())
    plotter = ScatterPlot(data)

    plotter.hovmoller('temperature')
    plotter.show()
    
if __name__ == '__main__':
    main()
