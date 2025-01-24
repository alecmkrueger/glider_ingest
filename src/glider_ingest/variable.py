from attrs import define, field, asdict
import pandas as pd

from glider_ingest.utils import get_wmo_id

@define
class Variable:
    """
    A class to represent a variable in a glider mission dataset.
    """
    # General attributes
    data_source_name: str|None = field(default=None)  # Name of the variable in the data source
    accuracy: float|None = field(default=None)
    ancillary_variables: str|None = field(default=None)
    instrument: str|None = field(default=None)
    long_name: str|None = field(default=None)  
    short_name: str|None = field(default=None)  # Name of the variable in the dataset, if it is changed from the data source
    observation_type: str|None = field(default=None)
    platform: str|None = field(default='platform')
    resolution: str|None|float = field(default=None)
    axis: str|None = field(default=None)
    bytes: str|None|int = field(default=None)
    comment: str|None = field(default=None)
    observation_type: str|None = field(default=None)
    platform: str|None = field(default=None)
    positive: str|None = field(default=None)
    precision: str|None|float = field(default=None)
    reference_datum: str|None = field(default=None)
    
    source_sensor: str|None = field(default=None)
    standard_name: str|None = field(default=None)
    units: str|None = field(default=None)
    valid_max: str|None|float = field(default=None)
    valid_min: str|None|float = field(default=None)
    update_time: str|None = field(default=None)
    coordinate_reference_frame: str|None = field(default=None)
    
    # Glider specific attributes
    id: str|None = field(default=None)
    wmo_id: str|None = field(default=None)
    instruments: str|None = field(default=None)
    type: str|None = field(default='platform')


    def __attrs_post_init__(self):
        """
        Post-initialization method to set the wmo_id attribute based on the id attribute.
        """
        # Generate update_time, long_name, and wmo_id if not given
        # Add current time to update_time if it was not given
        if self.update_time is None:
            self.update_time = pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')
        # Generate the long_name from the id if given
        if (self.long_name is None) & (self.id is not None):
            self.long_name = f'Slocum Glider {self.id}'
        # Generate the wmo_id from the id if given
        if (self.wmo_id is None) & (self.id is not None):
            self.wmo_id = get_wmo_id(self.id)
        if self.short_name is None:
            self.short_name = self.data_source_name
            
    def to_dict(self):
        """
        Convert the Variable object to a dictionary, sorted by key and filtered out None values.
        """
        # Return the dictionary sorted by key and filtered out None values
        return dict(sorted({key:value for key,value in asdict(self).items() if value is not None}.items()))


