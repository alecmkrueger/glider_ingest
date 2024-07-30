from glider_ingest.ingest import process
from pathlib import Path

# Example:
ds = process('540','Mission_44',extensions=['DBD','EBD'],raw_data_source=Path('../../test_data').resolve(),
             working_directory=Path('../../data').resolve(),output_nc_filename='test.nc',return_ds=True)

print(ds)