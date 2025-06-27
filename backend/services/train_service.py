"""Enhanced train service with dependency injection and better error handling."""

from typing import List, Optional
from models.TrainService import TrainService
from clients.rail_data_client import get_rail_data_client, RailDataClient
from core.logging import get_logger, LoggerMixin
from core.exceptions import DataParsingError, ExternalAPIError


class TrainDataService(LoggerMixin):
    """Service for retrieving and processing train data."""
    
    def __init__(self, rail_client: Optional[RailDataClient] = None):
        """
        Initialize the train data service.
        
        Args:
            rail_client: Optional rail data client (for dependency injection)
        """
        self.rail_client = rail_client or get_rail_data_client()
    
    def _parse_service_data(self, service_data: dict, is_arrival: bool = False) -> Optional[TrainService]:
        """
        Parse service data from the API response.
        
        Args:
            service_data: Raw service data from API
            is_arrival: Whether this is arrival data (affects time field names)
            
        Returns:
            TrainService object or None if parsing fails
        """
        try:
            # Determine time field names based on arrival/departure
            if is_arrival:
                scheduled_time_field = 'sta'
                expected_time_field = 'eta'
            else:
                scheduled_time_field = 'std'
                expected_time_field = 'etd'
            
            scheduled_time = service_data.get(scheduled_time_field)
            expected_time = service_data.get(expected_time_field)
            platform = service_data.get('platform')
            operator = service_data.get('operator')
            
            # Extract destination
            destination = None
            if service_data.get('destination'):
                destinations = service_data['destination']
                if destinations and len(destinations) > 0:
                    destination = destinations[0].get('locationName')
            
            # Extract origin
            origin = None
            if service_data.get('origin'):
                origins = service_data['origin']
                if origins and len(origins) > 0:
                    origin = origins[0].get('locationName')
            
            service_id = service_data.get('serviceID')
            status = expected_time  # Use expected time as status
            
            return TrainService(
                scheduled_time=scheduled_time or "",
                expected_time=expected_time or "",
                platform=platform,
                operator=operator,
                destination=destination,
                origin=origin,
                service_id=service_id,
                status=status
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing service data: {e}", exc_info=True)
            raise DataParsingError(f"Failed to parse service data: {e}")
    
    def get_arrivals(self, crs_code: str, num_rows: int = 5) -> List[TrainService]:
        """
        Get arrival services for a station.
        
        Args:
            crs_code: Station CRS code
            num_rows: Number of services to return
            
        Returns:
            List of TrainService objects
            
        Raises:
            ExternalAPIError: If API call fails
            DataParsingError: If response parsing fails
        """
        try:
            self.logger.info(f"Fetching arrivals for CRS: {crs_code}")
            
            # Get data from API
            data = self.rail_client.get_arrival_board_with_details(crs_code, num_rows)
            
            # Parse services
            services = []
            train_services = data.get('trainServices', [])
            
            for service_data in train_services:
                try:
                    service = self._parse_service_data(service_data, is_arrival=True)
                    if service:
                        services.append(service)
                except DataParsingError as e:
                    # Log parsing error but continue with other services
                    self.logger.warning(f"Skipping service due to parsing error: {e}")
                    continue
            
            self.logger.info(f"Successfully parsed {len(services)} arrivals for CRS: {crs_code}")
            return services
            
        except ExternalAPIError:
            # Re-raise API errors as-is
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching arrivals for {crs_code}: {e}", exc_info=True)
            raise ExternalAPIError(f"Failed to fetch arrivals for {crs_code}: {e}")
    
    def get_departures(self, crs_code: str, num_rows: int = 5) -> List[TrainService]:
        """
        Get departure services for a station.
        
        Args:
            crs_code: Station CRS code
            num_rows: Number of services to return
            
        Returns:
            List of TrainService objects
            
        Raises:
            ExternalAPIError: If API call fails
            DataParsingError: If response parsing fails
        """
        try:
            self.logger.info(f"Fetching departures for CRS: {crs_code}")
            
            # Get data from API
            data = self.rail_client.get_departure_board_with_details(crs_code, num_rows)
            
            # Parse services
            services = []
            train_services = data.get('trainServices', [])
            
            for service_data in train_services:
                try:
                    service = self._parse_service_data(service_data, is_arrival=False)
                    if service:
                        services.append(service)
                except DataParsingError as e:
                    # Log parsing error but continue with other services
                    self.logger.warning(f"Skipping service due to parsing error: {e}")
                    continue
            
            self.logger.info(f"Successfully parsed {len(services)} departures for CRS: {crs_code}")
            return services
            
        except ExternalAPIError:
            # Re-raise API errors as-is
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching departures for {crs_code}: {e}", exc_info=True)
            raise ExternalAPIError(f"Failed to fetch departures for {crs_code}: {e}")
    
    def get_service_details(self, service_id: str) -> Optional[dict]:
        """
        Get detailed information for a specific service.
        
        Args:
            service_id: The service ID to look up
            
        Returns:
            Service details dictionary or None if not found
            
        Note:
            This is a placeholder for future implementation when the API supports it
        """
        self.logger.info(f"Service details lookup requested for ID: {service_id}")
        # This would require additional API endpoints that may not be available
        # in the current Rail Data API
        return None
    
    def check_service_delays(self, services: List[TrainService], threshold_minutes: int = 5) -> List[TrainService]:
        """
        Filter services that are delayed beyond a threshold.
        
        Args:
            services: List of train services to check
            threshold_minutes: Minimum delay in minutes to be considered delayed
            
        Returns:
            List of delayed services
        """
        delayed_services = []
        
        for service in services:
            try:
                if service.scheduled_time and service.expected_time:
                    # This is a simplified check - in reality you'd need proper time parsing
                    # For now, we'll check if expected time is different from scheduled time
                    if service.expected_time != service.scheduled_time:
                        # Check if it's actually a delay (not early arrival/departure)
                        if service.expected_time not in ["On time", "Cancelled", "Delayed"]:
                            delayed_services.append(service)
                        elif service.expected_time == "Delayed":
                            delayed_services.append(service)
            except Exception as e:
                self.logger.warning(f"Error checking delay for service {service.service_id}: {e}")
                continue
        
        self.logger.info(f"Found {len(delayed_services)} delayed services out of {len(services)} total")
        return delayed_services
    
    def get_station_status(self, crs_code: str) -> dict:
        """
        Get overall status information for a station.
        
        Args:
            crs_code: Station CRS code
            
        Returns:
            Dictionary with station status information
        """
        try:
            arrivals = self.get_arrivals(crs_code, 10)
            departures = self.get_departures(crs_code, 10)
            
            delayed_arrivals = self.check_service_delays(arrivals)
            delayed_departures = self.check_service_delays(departures)
            
            return {
                "crs_code": crs_code,
                "total_arrivals": len(arrivals),
                "total_departures": len(departures),
                "delayed_arrivals": len(delayed_arrivals),
                "delayed_departures": len(delayed_departures),
                "status": "operational" if len(delayed_arrivals) + len(delayed_departures) == 0 else "delays"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting station status for {crs_code}: {e}", exc_info=True)
            return {
                "crs_code": crs_code,
                "status": "error",
                "error": str(e)
            }


# Global service instance
_train_service = None


def get_train_service() -> TrainDataService:
    """
    Get a singleton instance of the train data service.
    
    Returns:
        TrainDataService instance
    """
    global _train_service
    if _train_service is None:
        _train_service = TrainDataService()
    return _train_service


def set_train_service(service: TrainDataService):
    """
    Set the global train data service instance (useful for testing).
    
    Args:
        service: TrainDataService instance to use
    """
    global _train_service
    _train_service = service
