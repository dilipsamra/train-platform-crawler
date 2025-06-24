import pytest
import os
from utils.crs import station_name_to_crs, reload_station_crs
import tempfile


@pytest.fixture(autouse=True)
def setup_station_codes_csv(monkeypatch):
    # Use header keys that match the loader logic: stationName, crsCode
    csv_content = "stationName,crsCode\nAbbey Wood,ABW\n"
    temp_dir = tempfile.TemporaryDirectory()
    csv_path = f"{temp_dir.name}/station_codes.csv"
    with open(csv_path, "w") as f:
        f.write(csv_content)
    monkeypatch.setenv("STATION_CODES_CSV", csv_path)
    reload_station_crs()  # force reload after env var is set
    yield
    temp_dir.cleanup()


def test_station_name_to_crs_found():
    assert station_name_to_crs("Abbey Wood") == "ABW"


def test_station_name_to_crs_not_found():
    assert station_name_to_crs("Nonexistent Station") is None
