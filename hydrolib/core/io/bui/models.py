from typing import List, Callable, Any
from datetime import datetime, timedelta
from hydrolib.core.basemodel import BaseModel, FileModel
from .parser import BuiParser
from .serializer import write_bui_file

class BuiPrecipitationEvent(BaseModel):
    start_time: datetime
    timeseries_length: timedelta
    precipitation_per_timestep: List[List[float]]

class BuiPrecipitationEventList(BaseModel):
    precipitation_event_list: List[BuiPrecipitationEvent]

class BuiModel(FileModel):
    """
    Model that represents the file structure of a .bui file.

    Args:
        FileModel (BuiModel): Basemodel.

    Returns:
        BuiModel: New object containing data representing the .bui file.
    """

    default_dataset: int = 1 # Default value (always)
    number_of_stations: int
    name_of_stations: List[str]
    number_of_events: int
    seconds_per_timestep: int
    precipitation_events: BuiPrecipitationEventList
    # start_time: datetime
    # timeseries_length: timedelta
    # precipitation_per_timestep: List[List[float]]

    @classmethod
    def _filename(cls):
        return "bui_file"

    @classmethod
    def _ext(cls) -> str:
        return ".bui"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return write_bui_file

    @classmethod
    def _get_parser(cls) -> Callable:
        return BuiParser.parse
