from datetime import datetime, timedelta
import inspect
from tests.utils import test_input_dir, test_output_dir
from hydrolib.core.io.bui.parser import BuiParser, BuiEventParser
from hydrolib.core.io.bui.serializer import BuiSerializer, write_bui_file
from hydrolib.core.io.bui.models import BuiModel, BuiPrecipitationEvent, BuiPrecipitationEventList

def get_default_bui_model() -> BuiModel:   
    """
    Gets a well-tested basic BuiModel. 
    Wrapped in a method to avoid pytest failing to discover tests
    in case some code has been changed.

    Returns:
        BuiModel: Default bui model.
    """
    event_list = [BuiPrecipitationEvent(
        start_time = datetime(1996, 1, 1), # "1996 1 1 0 0 0 1 3 0 0"
        timeseries_length= timedelta(1, 10800),
        precipitation_per_timestep= [[0.2]]*9,
    )]
    precipitation_list = BuiPrecipitationEventList(
        precipitation_event_list=event_list
    )
    return BuiModel(
        filepath=test_input_dir / "rr_sample_trimmed" / "rr" / "default.bui",
        default_dataset = "1",
        number_of_stations= "1",
        name_of_stations= ["’Station1’"],
        number_of_events= "1",
        seconds_per_timestep = 10800,
        precipitation_events = precipitation_list)

class TestModel:
    def test_given_filepath_all_properties_loaded(self):
        test_file = test_input_dir / "rr_sample_trimmed" / "rr" / "default.bui"
        model = BuiModel(filepath=test_file)
        assert model == get_default_bui_model()
        assert model.filepath == test_file

    def test_save_default_and_load_returns_same_model(self):
        default_bui_model = get_default_bui_model()
        save_path = default_bui_model.save(test_output_dir)
        assert save_path.is_file()
        new_model = BuiModel(save_path)
        assert default_bui_model == new_model

        def filtered_dict(input_dict: dict) -> dict:
            return {k:v for k,v in input_dict.items() if k != "filepath"}
        assert filtered_dict(default_bui_model.dict()) == filtered_dict(new_model.dict())

class TestParser:

    def test_BuiParser_given_valid_file_parses_values(self):
        # 1. Define initial data.
        test_file = test_input_dir / "rr_sample_trimmed" / "rr" / "default.bui"
        assert test_file.is_file(), "Test File not found."

        # 2. Run test.
        dict_values = BuiParser.parse(test_file)

        # 3. Verify final expectations.
        default_bui_model = get_default_bui_model()
        assert dict_values is not None
        assert dict_values["default_dataset"] == str(default_bui_model.default_dataset)
        assert dict_values["number_of_stations"] == str(default_bui_model.number_of_stations)
        assert dict_values["name_of_stations"] == default_bui_model.name_of_stations
        assert dict_values["number_of_events"] == str(default_bui_model.number_of_events)
        assert dict_values["seconds_per_timestep"] == str(default_bui_model.seconds_per_timestep)
        assert dict_values["start_time"] == default_bui_model.start_time
        assert dict_values["precipitation_per_timestep"] == [list(map(str, v)) for v in default_bui_model.precipitation_per_timestep]

    def test_BuPrecipitationEventParser_given_valid_text(self):
        raw_text = inspect.cleandoc("""
            2021 12 20 0 0 0 1 0 4 20
            4.2
            4.2
        """)
        parsed_dict = BuiEventParser.parse(raw_text)
        assert parsed_dict["start_time"] == datetime(2021, 12, 20)
        assert parsed_dict["timeseries_length"] == timedelta(days=1, minutes=4, seconds=20)
        assert parsed_dict["precipitation_per_timestep"] == [["4.2"], ["4.2"]]


class TestSerializer:
    def test_BuiSerializer_given_dict_serialize_into_text(self):
        # 1. Define test data.
        dict_values = dict(
            filepath="my/custom/path",
            default_dataset = "1",
            number_of_stations= "1",
            name_of_stations= ["’Station1’"],
            number_of_events= "1",
            seconds_per_timestep= 10800,
            start_time= datetime(1996, 1, 1),
            timeseries_length=timedelta(1, 10800),
            precipitation_per_timestep= [["0.2"],["0.2"],["0.2"],["0.2"],])
        # Define expected datetime (it could fail by a second in a rare occasion)
        expected_datetime = datetime.now().strftime("%d-%m-%y %H:%M:%S")

        # 2. Do test.
        serialized_text = BuiSerializer.serialize(dict_values)

        # 3. Verify expectations.
        expected_serialized =  inspect.cleandoc("""
            *Name of this file: my/custom/path
            *Date and time of construction: {}
            *Comments are following an * (asterisk) and written above variables
            1
            *Number of stations
            1
            *Station Name
            ’Station1’
            *Number_of_events seconds_per_timestamp
            1 10800
            *Start datetime and number of timestamps in the format: yyyy#m#d:#h#m#s:#d#h#m#s
            *Observations per timestamp (row) and per station (column)
            1996 1 1 0 0 0 1 3 0 0
            0.2
            0.2
            0.2
            0.2
            """.format(expected_datetime))
        assert serialized_text == expected_serialized

    def test_BuiSerializer_given_station_ids_serialize_into_text(self):
        stations_ids = ["Hello", "World", "’Station1’"]
        serialized_text = BuiSerializer.serialize_stations_ids(stations_ids)
        assert serialized_text == "Hello World ’Station1’"

    def test_BuiSerializer_given_precipitation_serialize_into_text(self):
        precipitation_per_timestep= [["0.2"],["0.2"],["0.2"],["0.2"]]
        serialized_text = BuiSerializer.serialize_precipitation_per_timestep(precipitation_per_timestep)
        assert serialized_text == "0.2\n0.2\n0.2\n0.2"

    def test_BuiSerializer_given_start_time_serialize_into_text(self):
        first_event = datetime(2021, 12, 20, 0, 42, 24)
        expected_string = "2021 12 20 0 42 24"
        serialized_text = BuiSerializer.serialize_start_time(first_event)
        assert serialized_text == expected_string

    def test_BuiSerializer_given_timeseries_length_serialize_into_text(self):
        timeseries_length = timedelta(4, 2000)
        expected_string = "4 0 33 20"
        serialized_text = BuiSerializer.serialize_timeseries_length(timeseries_length)
        assert serialized_text == expected_string

    def test_write_bui_file_given_valid_file(self):
        default_bui_model = get_default_bui_model()
        new_path = test_output_dir / "new_path.bui"
        write_bui_file(new_path, default_bui_model.dict())
        assert new_path.is_file()
        written_text = new_path.read_text(encoding="utf8")
        assert str(new_path) in written_text
        assert str(default_bui_model.filepath) not in written_text
        new_path.unlink()
