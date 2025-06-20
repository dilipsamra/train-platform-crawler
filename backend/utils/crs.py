import csv
import os

# Utility for converting station names to CRS codes
# In production, use a full mapping or external API

STATION_CRS = {}
CSV_PATH = os.path.join(os.path.dirname(__file__), 'station_codes.csv')
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Skip empty or malformed rows
            if not row:
                continue
            # Defensive: handle possible None values in keys
            name_key = next((k for k in row if k and k.strip().lower() == 'stationname'), None)
            crs_key = next((k for k in row if k and k.strip().lower() == 'crscode'), None)
            if name_key and crs_key and row[name_key] and row[crs_key]:
                STATION_CRS[row[name_key].lower()] = row[crs_key]

def station_name_to_crs(name: str) -> str:
    return STATION_CRS.get(name.lower())
