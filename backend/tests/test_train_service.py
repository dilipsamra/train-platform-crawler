import os
os.environ['CONSUMER_KEY'] = 'dummy_key'

"""Tests for train service module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.train_service import TrainDataService, get_train_service, set_train_service
from models.TrainService import TrainService
from core.exceptions import DataParsingError, ExternalAPIError


class TestTrainDataService:
    """Test the TrainDataService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_rail_client = Mock()
        self.service = TrainDataService(rail_client=self.mock_rail_client)
    
    def test_parse_service_data_departure(self):
        """Test parsing departure service data."""
        service_data = {
            'std': '09:15',
            'etd': '09:20',
            'platform': '1',
            'operator': 'Great Western Railway',
            'destination': [{'locationName': 'Reading'}],
            'origin': [{'locationName': 'London Paddington'}],
            'serviceID': 'ABC123'
        }
        
        result = self.service._parse_service_data(service_data, is_arrival=False)
        
        assert result is not None
        assert result.scheduled_time == '09:15'
        assert result.expected_time == '09:20'
        assert result.platform == '1'
        assert result.operator == 'Great Western Railway'
        assert result.destination == 'Reading'
        assert result.origin == 'London Paddington'
        assert result.service_id == 'ABC123'
        assert result.status == '09:20'
    
    def test_parse_service_data_arrival(self):
        """Test parsing arrival service data."""
        service_data = {
            'sta': '10:30',
            'eta': 'On time',
            'platform': '2',
            'operator': 'CrossCountry',
            'destination': [{'locationName': 'Birmingham New Street'}],
            'origin': [{'locationName': 'Reading'}],
            'serviceID': 'XYZ789'
        }
        
        result = self.service._parse_service_data(service_data, is_arrival=True)
        
        assert result is not None
        assert result.scheduled_time == '10:30'
        assert result.expected_time == 'On time'
        assert result.platform == '2'
        assert result.operator == 'CrossCountry'
        assert result.destination == 'Birmingham New Street'
        assert result.origin == 'Reading'
        assert result.service_id == 'XYZ789'
        assert result.status == 'On time'
    
    def test_parse_service_data_missing_fields(self):
        """Test parsing service data with missing fields."""
        service_data = {
            'std': '09:15',
            'etd': '09:20'
            # Missing other fields
        }
        
        result = self.service._parse_service_data(service_data, is_arrival=False)
        
        assert result is not None
        assert result.scheduled_time == '09:15'
        assert result.expected_time == '09:20'
        assert result.platform is None
        assert result.operator is None
        assert result.destination is None
        assert result.origin is None
        assert result.service_id is None
    
    def test_parse_service_data_exception(self):
        """Test parsing service data that raises an exception."""
        # Invalid service data that will cause an exception
        service_data = None
        
        with pytest.raises(DataParsingError):
            self.service._parse_service_data(service_data, is_arrival=False)
    
    def test_get_arrivals_success(self):
        """Test successful retrieval of arrivals."""
        mock_response = {
            'trainServices': [
                {
                    'sta': '10:30',
                    'eta': 'On time',
                    'platform': '1',
                    'operator': 'GWR',
                    'destination': [{'locationName': 'Reading'}],
                    'origin': [{'locationName': 'London Paddington'}],
                    'serviceID': 'ABC123'
                },
                {
                    'sta': '10:45',
                    'eta': '10:50',
                    'platform': '2',
                    'operator': 'CrossCountry',
                    'destination': [{'locationName': 'Birmingham'}],
                    'origin': [{'locationName': 'Reading'}],
                    'serviceID': 'XYZ789'
                }
            ]
        }
        
        self.mock_rail_client.get_arrival_board_with_details.return_value = mock_response
        
        result = self.service.get_arrivals('PAD', 5)
        
        assert len(result) == 2
        assert all(isinstance(service, TrainService) for service in result)
        assert result[0].scheduled_time == '10:30'
        assert result[1].scheduled_time == '10:45'
        
        self.mock_rail_client.get_arrival_board_with_details.assert_called_once_with('PAD', 5)
    
    def test_get_departures_success(self):
        """Test successful retrieval of departures."""
        mock_response = {
            'trainServices': [
                {
                    'std': '09:15',
                    'etd': '09:20',
                    'platform': '1',
                    'operator': 'GWR',
                    'destination': [{'locationName': 'Reading'}],
                    'origin': [{'locationName': 'London Paddington'}],
                    'serviceID': 'ABC123'
                }
            ]
        }
        
        self.mock_rail_client.get_departure_board_with_details.return_value = mock_response
        
        result = self.service.get_departures('PAD', 5)
        
        assert len(result) == 1
        assert isinstance(result[0], TrainService)
        assert result[0].scheduled_time == '09:15'
        
        self.mock_rail_client.get_departure_board_with_details.assert_called_once_with('PAD', 5)
    
    def test_get_arrivals_api_error(self):
        """Test handling of API errors when getting arrivals."""
        self.mock_rail_client.get_arrival_board_with_details.side_effect = ExternalAPIError("API Error")
        
        with pytest.raises(ExternalAPIError):
            self.service.get_arrivals('PAD', 5)
    
    def test_get_departures_api_error(self):
        """Test handling of API errors when getting departures."""
        self.mock_rail_client.get_departure_board_with_details.side_effect = ExternalAPIError("API Error")
        
        with pytest.raises(ExternalAPIError):
            self.service.get_departures('PAD', 5)
    
    def test_get_arrivals_parsing_error(self):
        """Test handling of parsing errors in arrivals."""
        mock_response = {
            'trainServices': [
                None,  # This will cause a parsing error
                {
                    'sta': '10:30',
                    'eta': 'On time',
                    'platform': '1',
                    'operator': 'GWR',
                    'destination': [{'locationName': 'Reading'}],
                    'origin': [{'locationName': 'London Paddington'}],
                    'serviceID': 'ABC123'
                }
            ]
        }
        
        self.mock_rail_client.get_arrival_board_with_details.return_value = mock_response
        
        # Should skip the invalid service and return the valid one
        result = self.service.get_arrivals('PAD', 5)
        
        assert len(result) == 1
        assert result[0].scheduled_time == '10:30'
    
    def test_check_service_delays(self):
        """Test checking for delayed services."""
        services = [
            TrainService(
                scheduled_time='09:15',
                expected_time='09:20',  # 5 min delay
                platform='1',
                operator='GWR',
                destination='Reading',
                origin='London',
                service_id='ABC123',
                status='09:20'
            ),
            TrainService(
                scheduled_time='09:30',
                expected_time='On time',
                platform='2',
                operator='GWR',
                destination='Reading',
                origin='London',
                service_id='DEF456',
                status='On time'
            ),
            TrainService(
                scheduled_time='09:45',
                expected_time='Delayed',
                platform='3',
                operator='GWR',
                destination='Reading',
                origin='London',
                service_id='GHI789',
                status='Delayed'
            )
        ]
        
        delayed = self.service.check_service_delays(services, threshold_minutes=5)
        
        # Should find 2 delayed services (one with different time, one marked as "Delayed")
        assert len(delayed) == 2
        assert delayed[0].service_id == 'ABC123'
        assert delayed[1].service_id == 'GHI789'
    
    def test_get_station_status_success(self):
        """Test getting station status successfully."""
        # Mock arrivals
        arrivals_response = {
            'trainServices': [
                {
                    'sta': '10:30',
                    'eta': 'On time',
                    'platform': '1',
                    'operator': 'GWR',
                    'destination': [{'locationName': 'Reading'}],
                    'origin': [{'locationName': 'London Paddington'}],
                    'serviceID': 'ABC123'
                }
            ]
        }
        
        # Mock departures
        departures_response = {
            'trainServices': [
                {
                    'std': '09:15',
                    'etd': '09:20',  # Delayed
                    'platform': '1',
                    'operator': 'GWR',
                    'destination': [{'locationName': 'Reading'}],
                    'origin': [{'locationName': 'London Paddington'}],
                    'serviceID': 'DEF456'
                }
            ]
        }
        
        self.mock_rail_client.get_arrival_board_with_details.return_value = arrivals_response
        self.mock_rail_client.get_departure_board_with_details.return_value = departures_response
        
        result = self.service.get_station_status('PAD')
        
        assert result['crs_code'] == 'PAD'
        assert result['total_arrivals'] == 1
        assert result['total_departures'] == 1
        assert result['delayed_arrivals'] == 0
        assert result['delayed_departures'] == 1
        assert result['status'] == 'delays'
    
    def test_get_station_status_error(self):
        """Test getting station status with error."""
        self.mock_rail_client.get_arrival_board_with_details.side_effect = ExternalAPIError("API Error")
        
        result = self.service.get_station_status('PAD')
        
        assert result['crs_code'] == 'PAD'
        assert result['status'] == 'error'
        assert 'error' in result
    
    def test_get_service_details(self):
        """Test getting service details (placeholder implementation)."""
        result = self.service.get_service_details('ABC123')
        
        # Currently returns None as it's a placeholder
        assert result is None


class TestTrainServiceSingleton:
    """Test the singleton functions for train service."""
    
    @patch('core.config.get_settings')
    @patch('core.config.Settings')
    def test_get_train_service_singleton(self, mock_settings, mock_get_settings):
        from core.config import get_settings
        get_settings.cache_clear()
        from services.train_service import get_train_service
        service1 = get_train_service()
        service2 = get_train_service()
        assert service1 is service2
    
    def test_set_train_service(self):
        """Test setting a custom train service instance."""
        mock_service = Mock(spec=TrainDataService)
        
        set_train_service(mock_service)
        
        result = get_train_service()
        assert result is mock_service
        
        # Clean up - reset to None so other tests aren't affected
        set_train_service(None)
