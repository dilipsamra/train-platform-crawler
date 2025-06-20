import os
from zeep import Client
from zeep.transports import Transport
from models.TrainService import TrainService
import logging

logger = logging.getLogger("train-platform-crawler.national_rail")

DARWIN_TOKEN = os.getenv("DARWIN_TOKEN")
WSDL_URL = "https://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx"


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
    client = Client(wsdl=WSDL_URL, transport=Transport())
    header = {"AccessToken": {"TokenValue": DARWIN_TOKEN}}
    try:
        logger.info(f"Requesting arrivals for CRS: {crs_code}")
        response = client.service.GetArrivalBoard(numRows=5, crs=crs_code, _soapheaders=header)
        services = []
        if hasattr(response, 'trainServices') and response.trainServices and hasattr(response.trainServices, 'service'):
            for svc in response.trainServices.service:
                parsed = _parse_service(svc)
                if parsed:
                    services.append(parsed)
        logger.info(f"Found {len(services)} arrivals for CRS: {crs_code}")
        return services
    except Exception as e:
        logger.error(f"Error fetching arrivals for {crs_code}: {e}", exc_info=True)
        return []

def get_departures(crs_code: str):
    client = Client(wsdl=WSDL_URL, transport=Transport())
    header = {"AccessToken": {"TokenValue": DARWIN_TOKEN}}
    try:
        logger.info(f"Requesting departures for CRS: {crs_code}")
        response = client.service.GetDepartureBoard(numRows=5, crs=crs_code, _soapheaders=header)
        services = []
        if hasattr(response, 'trainServices') and response.trainServices and hasattr(response.trainServices, 'service'):
            for svc in response.trainServices.service:
                parsed = _parse_service(svc)
                if parsed:
                    services.append(parsed)
        logger.info(f"Found {len(services)} departures for CRS: {crs_code}")
        return services
    except Exception as e:
        logger.error(f"Error fetching departures for {crs_code}: {e}", exc_info=True)
        return []
