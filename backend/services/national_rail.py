import os
from models.TrainService import TrainService
from services.ldbws_rest import get_dep_board_with_details, get_arr_board_with_details
import logging

# Use the new endpoint from environment or default to the Rail Data Marketplace endpoint
BASE_URL = os.getenv("LDBWS_BASE_URL", "https://api1.raildata.org.uk/1010-live-departure-board-dep1_2/LDBWS/api/20220120")


logger = logging.getLogger("train-platform-crawler.national_rail")


def _parse_service(svc):
    try:
        scheduled_time = getattr(svc, 'std', None)
        expected_time = getattr(svc, 'etd', None)
        platform = getattr(svc, 'platform', None)
        operator = getattr(svc, 'operator', None)
        destination = None
        if hasattr(svc, 'destination') and svc.destination and hasattr(svc.destination, 'location'):
            destination = svc.destination.location[0].locationName
        origin = None
        if hasattr(svc, 'origin') and svc.origin and hasattr(svc.origin, 'location'):
            origin = svc.origin.location[0].locationName
        service_id = getattr(svc, 'serviceID', None)
        status = expected_time
        return TrainService(
            scheduled_time=scheduled_time,
            expected_time=expected_time,
            platform=platform,
            operator=operator,
            destination=destination,
            origin=origin,
            service_id=service_id,
            status=status
        )
    except Exception as e:
        logger.error(f"Error parsing service: {e}", exc_info=True)
        return None


def get_arrivals(crs_code: str):
    try:
        logger.info(f"Requesting arrivals for CRS: {crs_code} via REST API")
        data = get_arr_board_with_details(crs_code, numRows=5, base_url=BASE_URL)
        services = []
        for svc in (data.get('trainServices') or []):
            scheduled_time = svc.get('sta')
            expected_time = svc.get('eta')
            platform = svc.get('platform')
            operator = svc.get('operator')
            destination = svc.get('destination', [{}])[0].get('locationName') if svc.get('destination') else None
            origin = svc.get('origin', [{}])[0].get('locationName') if svc.get('origin') else None
            service_id = svc.get('serviceID')
            status = expected_time
            services.append(TrainService(
                scheduled_time=scheduled_time,
                expected_time=expected_time,
                platform=platform,
                operator=operator,
                destination=destination,
                origin=origin,
                service_id=service_id,
                status=status
            ))
        logger.info(f"Found {len(services)} arrivals for CRS: {crs_code}")
        return services
    except Exception as e:
        logger.error(f"Error fetching arrivals for {crs_code}: {e}", exc_info=True)
        return []


def get_departures(crs_code: str):
    try:
        logger.info(f"Requesting departures for CRS: {crs_code} via REST API")
        data = get_dep_board_with_details(crs_code, numRows=5, base_url=BASE_URL)
        services = []
        for svc in (data.get('trainServices') or []):
            scheduled_time = svc.get('std')
            expected_time = svc.get('etd')
            platform = svc.get('platform')
            operator = svc.get('operator')
            destination = svc.get('destination', [{}])[0].get('locationName') if svc.get('destination') else None
            origin = svc.get('origin', [{}])[0].get('locationName') if svc.get('origin') else None
            service_id = svc.get('serviceID')
            status = expected_time
            services.append(TrainService(
                scheduled_time=scheduled_time,
                expected_time=expected_time,
                platform=platform,
                operator=operator,
                destination=destination,
                origin=origin,
                service_id=service_id,
                status=status
            ))
        logger.info(f"Found {len(services)} departures for CRS: {crs_code}")
        return services
    except Exception as e:
        logger.error(f"Error fetching departures for {crs_code}: {e}", exc_info=True)
        return []

# Optionally, you can implement get_arrivals similarly using the REST API's GetArrivalBoard endpoint.
