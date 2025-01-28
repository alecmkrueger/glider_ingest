from pathlib import Path

from glider_ingest import Processor

def main():
    memory_card_copy_path = Path('path/to/memory/card/copy')
    # Where you want the netcdf to be saved to
    working_dir = Path('path/to/working/dir').resolve()
    mission_num = '46'

    # Init a processor object
    processor = Processor(memory_card_copy_path=memory_card_copy_path,
                          working_dir=working_dir,
                          mission_num=mission_num)
    # Rename the latitude and longitude short names to be 'lat' and 'lon'
    processor.mission_vars['m_lat'].short_name = 'lat'
    processor.mission_vars['m_lon'].short_name = 'lon'
    # Add custom variables to the mission_data container using strings
    processor.add_variables(variables=['m_water_vx','m_water_vy'])
    # Save to a netcdf file
    processor.save()

if __name__ == '__main__':
    main()
