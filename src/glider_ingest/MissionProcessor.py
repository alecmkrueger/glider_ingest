from attrs import define

from glider_ingest.MissionData import MissionData
from glider_ingest.ScienceProcessor import ScienceProcessor
from glider_ingest.FlightProcessor import FlightProcessor
from glider_ingest.utils import add_gridded_data


@define
class MissionProcessor:
    """
    A class to process and manage mission data for glider operations.

    This class integrates data from science and flight logs, combines them
    into a mission dataset, and saves the processed data to a NetCDF file.

    Attributes
    ----------
    mission_data : MissionData
        An instance of the MissionData class containing mission-related configurations and paths.
    """

    mission_data: MissionData

    def process_sci(self):
        """
        Process science data for the mission.

        This method initializes a ScienceProcessor, processes the science data,
        and updates the mission data with the processed results.

        Returns
        -------
        MissionData
            Updated mission data after processing science data.
        """
        # Initialize and run the science data processor
        sci_processor = ScienceProcessor(mission_data=self.mission_data)
        sci_processor.process_sci_data()
        return sci_processor.mission_data

    def process_fli(self):
        """
        Process flight data for the mission.

        This method initializes a FlightProcessor, processes the flight data,
        and updates the mission data with the processed results.

        Returns
        -------
        MissionData
            Updated mission data after processing flight data.
        """
        # Initialize and run the flight data processor
        fli_processor = FlightProcessor(mission_data=self.mission_data)
        fli_processor.process_flight_data()
        return fli_processor.mission_data

    def generate_mission_dataset(self):
        """
        Generate the mission dataset by combining science and flight data.

        This method performs the following steps:
        1. Sets up mission metadata.
        2. Processes science and flight data.
        3. Combines science and flight datasets into a mission dataset.
        4. Adds gridded data and global attributes to the mission dataset.

        Raises
        ------
        AttributeError
            If `self.mission_data` does not contain the necessary data for processing.
        """
        # Set up the mission metadata and paths
        self.mission_data.setup()

        # Process science and flight data
        self.mission_data = self.process_sci()
        self.mission_data = self.process_fli()

        # Combine science and flight datasets into the mission dataset
        self.mission_data.ds_mission = self.mission_data.ds_sci.copy()
        self.mission_data.ds_mission.update(self.mission_data.ds_fli)

        # Add gridded data to the mission dataset
        self.mission_data.ds_mission = add_gridded_data(self.mission_data.ds_mission)

        # Add global attributes to the mission dataset
        self.mission_data.add_attrs()

    def save_mission_dataset(self):
        """
        Save the mission dataset to a NetCDF file.

        This method generates the mission dataset if it has not already been created
        and saves the dataset to the configured output NetCDF file.

        Raises
        ------
        AttributeError
            If `self.mission_data` does not contain a mission dataset to save.
        """
        # Ensure the mission dataset is generated
        if not hasattr(self.mission_data, 'ds_mission'):
            self.generate_mission_dataset()

        # Save the mission dataset to the specified NetCDF path
        self.mission_data.ds_mission.to_netcdf(self.mission_data.output_nc_path, engine='netcdf4')

        
