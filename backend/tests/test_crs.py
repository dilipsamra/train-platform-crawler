import pytest
from utils.crs import station_name_to_crs


def test_station_name_to_crs_found():
    assert station_name_to_crs("Abbey Wood") == "ABW"

def test_station_name_to_crs_not_found():
    assert station_name_to_crs("Nonexistent Station") is None
