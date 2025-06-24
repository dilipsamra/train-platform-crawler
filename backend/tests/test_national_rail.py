import pytest
from unittest.mock import patch, MagicMock
from services import national_rail

@patch("services.ldbws_rest.get_arr_board_with_details")
def test_get_arrivals_returns_services(mock_get_arr_board_with_details):
    # Mock the REST response structure
    mock_service = {
        "sta": "10:00",
        "eta": "10:05",
        "platform": "5",
        "operator": "Avanti West Coast",
        "destination": [{"locationName": "Manchester Piccadilly"}],
        "origin": [{"locationName": "London Euston"}],
        "serviceID": "A1"
    }
    mock_get_arr_board_with_details.return_value = {"trainServices": [mock_service]}

    result = national_rail.get_arrivals("EUS")
    assert len(result) == 1
    assert result[0].destination == "Manchester Piccadilly"
    assert result[0].origin == "London Euston"

@patch("services.ldbws_rest.get_arr_board_with_details")
def test_get_arrivals_handles_exception(mock_get_arr_board_with_details):
    mock_get_arr_board_with_details.side_effect = Exception("API error")
    result = national_rail.get_arrivals("EUS")
    assert result == []
