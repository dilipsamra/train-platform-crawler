import pytest
import os
from utils.crs import station_name_to_crs
import tempfile


@pytest.fixture(autouse=True)
def setup_station_codes_csv(monkeypatch):
    # Create a minimal CSV for testing
    csv_content = "Station Name,CRS Code\nAbbey Wood,ABW\n"
    temp_dir = tempfile.TemporaryDirectory()
    csv_path = f"{temp_dir.name}/station_codes.csv"
    with open(csv_path, "w") as f:
        f.write(csv_content)
    monkeypatch.setenv("STATION_CODES_CSV", csv_path)
    yield
    temp_dir.cleanup()


def test_station_name_to_crs_found():
    assert station_name_to_crs("Abbey Wood") == "ABW"


def test_station_name_to_crs_not_found():
    assert station_name_to_crs("Nonexistent Station") is None
