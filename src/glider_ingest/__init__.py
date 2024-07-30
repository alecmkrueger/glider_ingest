'''
Module to ingest and process raw glider data into NetCDF files
'''

from .processor import Processor
from .utils import utils
from .gridder import Gridder
from .ingest import ingest