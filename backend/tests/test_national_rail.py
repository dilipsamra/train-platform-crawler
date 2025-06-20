import pytest
from unittest.mock import patch, MagicMock
from services import national_rail

@patch("services.national_rail.Client")
def test_get_arrivals_returns_services(mock_client):
    # Mock the SOAP response structure
    mock_service = MagicMock()
    mock_service.std = "10:00"
    mock_service.etd = "10:05"
    mock_service.platform = "5"
    mock_service.operator = "Avanti West Coast"
    mock_service.destination.location = [MagicMock(locationName="Manchester Piccadilly")]
    mock_service.origin.location = [MagicMock(locationName="London Euston")]
    mock_service.serviceID = "A1"
    
    mock_train_services = MagicMock()
    mock_train_services.service = [mock_service]
    mock_response = MagicMock()
    mock_response.trainServices = mock_train_services
    mock_client.return_value.service.GetArrivalBoard.return_value = mock_response

    result = national_rail.get_arrivals("EUS")
    assert len(result) == 1
    assert result[0].destination == "Manchester Piccadilly"
    assert result[0].origin == "London Euston"

@patch("services.national_rail.Client")
def test_get_arrivals_handles_exception(mock_client):
    mock_client.return_value.service.GetArrivalBoard.side_effect = Exception("API error")
    result = national_rail.get_arrivals("EUS")
    assert result == []
