from attrs import define, field, asdict
import pandas as pd

from .utils import get_wmo_id

@define
class Variable:
    """
    A class to represent a variable in a glider mission dataset.
    """
    # Required attributes
    data_source_name: str|None = field(default=None)  # Name of the variable in the data source
    _short_name: str|None = field(default=None)  # Name of the variable in the dataset, if it is changed from the data source
    # Optional attributes
    accuracy: float|None = field(default=None)
    ancillary_variables: str|None = field(default=None)
    instrument: str|None = field(default=None)
    _long_name: str|None = field(default=None)
    observation_type: str|None = field(default=None)
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
    _update_time: str|None = field(default=None)
    coordinate_reference_frame: str|None = field(default=None)
    source: str|None = field(default=None)  # Where the gridded variable came from

    # Default attributes
    platform: str|None = field(default='platform')

    # Variable operation attributes
    to_grid: bool|str = field(default=False)  # If you want the variable to be gridded: True

    # Glider specific attributes
    id: str|None = field(default=None)
    _wmo_id: str|None = field(default=None)
    instruments: str|None = field(default=None)
    type: str|None = field(default='platform')

    def __post_init__(self):
        """Validate that at least one of short_name or data_source_name is provided."""
        if self.data_source_name is None and self._short_name is None:
            raise ValueError("Either 'short_name' or 'data_source_name' must be provided")

    @property
    def update_time(self) -> str:
        if self._update_time is None:
            return pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')
        return self._update_time

    @update_time.setter
    def update_time(self, value):
        self._update_time = value

    @property
    def long_name(self) -> str|None:
        if self._long_name is None and self.id is not None:
            return f'Slocum Glider {self.id}'
        return self._long_name

    @long_name.setter
    def long_name(self, value):
        self._long_name = value

    @property
    def wmo_id(self) -> str|None:
        if self._wmo_id is None and self.id is not None:
            return get_wmo_id(self.id)
        return self._wmo_id

    @wmo_id.setter
    def wmo_id(self, value):
        self._wmo_id = value

    @property
    def short_name(self) -> str|None:
        if self._short_name is None:
            return self.data_source_name
        return self._short_name

    @short_name.setter
    def short_name(self, value):
        self._short_name = value

    @property
    def calculated(self) -> bool:
        if self.data_source_name is None:
            return True
        return False

    @calculated.setter
    def calculated(self, value):
        self._calculated = value


    def _filter_out_keys(self):
        """
        Filter out keys from the Variable object that are None.
        """
        # Return the dictionary sorted by key and filtered out None values

        # Convert to_grid to string for JSON serialization
        self.to_grid = f'{self.to_grid}'
        self.data_source_name = str(self.data_source_name)

        return {key:value for key,value in asdict(self).items() if value is not None}

    def to_dict(self):
        """
        Convert the Variable object to a dictionary, sorted by key and filtered out None values.
        """
        # Return the dictionary sorted by key and filtered out None values
        return dict(sorted(self._filter_out_keys().items()))


