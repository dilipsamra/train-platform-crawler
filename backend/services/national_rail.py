import os
from zeep import Client
from zeep.transports import Transport
from models.TrainService import TrainService

DARWIN_TOKEN = os.getenv("DARWIN_TOKEN")
WSDL_URL = "https://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx"


def _parse_service(svc):
    # Defensive parsing for all fields
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
        # Optionally log the error
        return None

def get_arrivals(crs_code: str):
    client = Client(wsdl=WSDL_URL, transport=Transport())
    header = {"AccessToken": {"TokenValue": DARWIN_TOKEN}}
    try:
        response = client.service.GetArrivalBoard(numRows=5, crs=crs_code, _soapheaders=header)
        services = []
        if hasattr(response, 'trainServices') and response.trainServices and hasattr(response.trainServices, 'service'):
            for svc in response.trainServices.service:
                parsed = _parse_service(svc)
                if parsed:
                    services.append(parsed)
        return services
    except Exception as e:
        # Optionally log the error
        return []

def get_departures(crs_code: str):
    client = Client(wsdl=WSDL_URL, transport=Transport())
    header = {"AccessToken": {"TokenValue": DARWIN_TOKEN}}
    try:
        response = client.service.GetDepartureBoard(numRows=5, crs=crs_code, _soapheaders=header)
        services = []
        if hasattr(response, 'trainServices') and response.trainServices and hasattr(response.trainServices, 'service'):
            for svc in response.trainServices.service:
                parsed = _parse_service(svc)
                if parsed:
                    services.append(parsed)
        return services
    except Exception as e:
        # Optionally log the error
        return []
