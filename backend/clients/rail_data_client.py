"""Rail Data API client with proper error handling and configuration management."""

import time
from typing import Optional, Dict, Any
import requests
from requests.auth import HTTPBasicAuth

from core.config import get_settings
from core.exceptions import (
    ExternalAPIError, 
    APITimeoutError, 
    APIRateLimitError,
    ConfigurationError,
    handle_api_error
)
from core.logging import get_logger, log_api_request, LoggerMixin


class RailDataClient(LoggerMixin):
    """Client for interacting with the Rail Data API."""
    
    def __init__(self, settings=None):
        """
        Initialize the Rail Data API client.
        
        Args:
            settings: Optional settings override (useful for testing)
        """
        self.settings = settings or get_settings()
        self._validate_configuration()
        
        # Set up session for connection pooling
        self.session = requests.Session()
        self._setup_authentication()
        
        # Default timeouts
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
    
    def _validate_configuration(self):
        """Validate that required configuration is present."""
        if not self.settings.consumer_key:
            raise ConfigurationError("CONSUMER_KEY is required for Rail Data API access")
        
        if not self.settings.ldbws_base_url:
            raise ConfigurationError("LDBWS_BASE_URL is required for Rail Data API access")
    
    def _setup_authentication(self):
        """Set up authentication for the API client."""
        if self.settings.consumer_secret:
            # Use HTTP Basic Auth if secret is provided
            self.session.auth = HTTPBasicAuth(
                self.settings.consumer_key, 
                self.settings.consumer_secret
            )
        else:
            # Use API key header
            self.session.headers.update({
                "x-apikey": self.settings.consumer_key,
                "User-Agent": f"{self.settings.app_name}/{self.settings.app_version}",
                "Accept": "application/json"
            })
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        retries: int = 0
    ) -> Dict[str, Any]:
        """
        Make a request to the Rail Data API with error handling and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            retries: Current retry count
            
        Returns:
            JSON response data
            
        Raises:
            Various APIClientError subclasses based on the error type
        """
        url = f"{self.settings.ldbws_base_url}/{endpoint.lstrip('/')}"
        
        # Clean up parameters (remove None values)
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        
        start_time = time.time()
        
        try:
            self.logger.debug(f"Making {method} request to {url} with params: {params}")
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            log_api_request(method, url, response.status_code, response_time)
            
            # Handle different response status codes
            if response.status_code == 200:
                return response.json()
            else:
                handle_api_error(response.status_code, response.text, url)
                
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            log_api_request(method, url, 504, response_time)
            
            if retries < self.max_retries:
                self.logger.warning(f"Request timeout, retrying ({retries + 1}/{self.max_retries})")
                time.sleep(self.retry_delay * (retries + 1))
                return self._make_request(method, endpoint, params, retries + 1)
            
            raise APITimeoutError(f"Request to {url} timed out after {self.max_retries} retries")
            
        except requests.exceptions.ConnectionError as e:
            response_time = time.time() - start_time
            log_api_request(method, url, 0, response_time)
            
            if retries < self.max_retries:
                self.logger.warning(f"Connection error, retrying ({retries + 1}/{self.max_retries})")
                time.sleep(self.retry_delay * (retries + 1))
                return self._make_request(method, endpoint, params, retries + 1)
            
            raise ExternalAPIError(f"Connection error when calling {url}: {e}")
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            log_api_request(method, url, 0, response_time)
            raise ExternalAPIError(f"Request error when calling {url}: {e}")
    
    def get_departure_board(
        self, 
        crs: str, 
        num_rows: int = 10, 
        filter_crs: Optional[str] = None,
        filter_type: str = "to", 
        time_offset: int = 0, 
        time_window: int = 120
    ) -> Dict[str, Any]:
        """
        Get departure board for a station.
        
        Args:
            crs: Station CRS code
            num_rows: Number of services to return
            filter_crs: Filter by destination CRS code
            filter_type: Filter type ("to" or "from")
            time_offset: Time offset in minutes
            time_window: Time window in minutes
            
        Returns:
            Departure board data
        """
        params = {
            "numRows": num_rows,
            "filterCrs": filter_crs,
            "filterType": filter_type,
            "timeOffset": time_offset,
            "timeWindow": time_window
        }
        
        return self._make_request("GET", f"GetDepartureBoard/{crs}", params)
    
    def get_departure_board_with_details(
        self, 
        crs: str, 
        num_rows: int = 10
    ) -> Dict[str, Any]:
        """
        Get detailed departure board for a station.
        
        Args:
            crs: Station CRS code
            num_rows: Number of services to return
            
        Returns:
            Detailed departure board data
        """
        params = {"numRows": num_rows}
        return self._make_request("GET", f"GetDepBoardWithDetails/{crs}", params)
    
    def get_arrival_board_with_details(
        self, 
        crs: str, 
        num_rows: int = 10,
        filter_crs: Optional[str] = None,
        filter_type: str = "to", 
        time_offset: int = 0, 
        time_window: int = 120
    ) -> Dict[str, Any]:
        """
        Get detailed arrival board for a station.
        
        Args:
            crs: Station CRS code
            num_rows: Number of services to return
            filter_crs: Filter by origin CRS code
            filter_type: Filter type ("to" or "from")
            time_offset: Time offset in minutes
            time_window: Time window in minutes
            
        Returns:
            Detailed arrival board data
        """
        params = {
            "numRows": num_rows,
            "filterCrs": filter_crs,
            "filterType": filter_type,
            "timeOffset": time_offset,
            "timeWindow": time_window
        }
        
        return self._make_request("GET", f"GetArrBoardWithDetails/{crs}", params)
    
    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global client instance (can be overridden for testing)
_client_instance = None


def get_rail_data_client() -> RailDataClient:
    """
    Get a singleton instance of the Rail Data API client.
    
    Returns:
        RailDataClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = RailDataClient()
    return _client_instance


def set_rail_data_client(client: RailDataClient):
    """
    Set the global Rail Data API client instance (useful for testing).
    
    Args:
        client: RailDataClient instance to use
    """
    global _client_instance
    _client_instance = client
