import os
import requests
from requests.auth import HTTPBasicAuth

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")  # Optional, if required

def get_departure_board(crs, numRows=10, filterCrs=None, filterType="to", timeOffset=0, timeWindow=120, base_url=None):
    if base_url is None:
        base_url = os.getenv("LDBWS_BASE_URL")
    url = f"{base_url}/GetDepartureBoard/{crs}"
    params = {
        "numRows": numRows,
        "filterCrs": filterCrs,
        "filterType": filterType,
        "timeOffset": timeOffset,
        "timeWindow": timeWindow
    }
    params = {k: v for k, v in params.items() if v is not None}
    if CONSUMER_SECRET:
        auth = HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET)
        response = requests.get(url, params=params, auth=auth)
    else:
        headers = {"x-apikey": CONSUMER_KEY}
        print(f"Requesting URL: {url} with headers: {headers}")
        response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

def get_dep_board_with_details(crs, numRows=10, base_url=None):
    if base_url is None:
        base_url = os.getenv("LDBWS_BASE_URL")
    url = f"{base_url}/GetDepBoardWithDetails/{crs}"
    params = {"numRows": numRows}
    headers = {
        "x-apikey": CONSUMER_KEY,
        "User-Agent": "curl/7.88.1",
        "Accept": "*/*"
    }
    print(f"Requesting URL: {url} with headers: {headers} and params: {params}")
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

def get_arr_board_with_details(crs, numRows=10, filterCrs=None, filterType="to", timeOffset=0, timeWindow=120, base_url=None):
    if base_url is None:
        base_url = os.getenv("LDBWS_BASE_URL")
    url = f"{base_url}/GetArrBoardWithDetails/{crs}"
    params = {
        "numRows": numRows,
        "filterCrs": filterCrs,
        "filterType": filterType,
        "timeOffset": timeOffset,
        "timeWindow": timeWindow
    }
    params = {k: v for k, v in params.items() if v is not None}
    if CONSUMER_SECRET:
        auth = HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET)
        response = requests.get(url, params=params, auth=auth)
    else:
        headers = {"x-apikey": CONSUMER_KEY}
        print(f"Requesting URL: {url} with headers: {headers}")
        response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

# Example usage:
# data = get_departure_board("KGX")
# print(data)
