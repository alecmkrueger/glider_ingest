from attrs import define, field
from pathlib import Path


@define
class Processor:
    raw_data_source:Path
    working_directory:Path

    