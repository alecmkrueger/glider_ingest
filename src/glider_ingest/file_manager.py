from attrs import define, field
from pathlib import Path
import xarray as xr

from glider_ingest.utils import find_nth
from glider_ingest.processor import Processor


@define
class FileManager:
    """
    A class to manage files and directories.
    """
    
    processor: Processor
