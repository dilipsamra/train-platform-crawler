import csv
import os
import logging

logger = logging.getLogger("train-platform-crawler.crs")

STATION_CRS = {}

def _load_station_crs():
    csv_path = os.getenv("STATION_CODES_CSV", os.path.join(os.path.dirname(__file__), 'station_codes.csv'))
    if os.path.exists(csv_path):
        try:
            with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
                # Skip comment lines before the header
                while True:
                    pos = csvfile.tell()
                    line = csvfile.readline()
                    if not line.startswith("#"):
                        csvfile.seek(pos)
                        break
                reader = csv.DictReader(csvfile)
                print("CSV header keys:", reader.fieldnames)
                for row in reader:
                    if not row:
                        continue
                    name_key = next((k for k in row if k and k.strip().lower() == 'stationname'), None)
                    crs_key = next((k for k in row if k and k.strip().lower() == 'crscode'), None)
                    if name_key and crs_key and row[name_key] and row[crs_key]:
                        key = row[name_key].strip().lower()
                        value = row[crs_key].strip().upper()
                        STATION_CRS[key] = value
                print("Loaded station keys:", list(STATION_CRS.keys())[:10])
            logger.info(f"Loaded {len(STATION_CRS)} station CRS codes. Example keys: {list(STATION_CRS.keys())[:5]}")
        except Exception as e:
            logger.error(f"Error loading CRS CSV: {e}", exc_info=True)
    else:
        logger.warning(f"CRS CSV file not found at {csv_path}")

_load_station_crs()

def station_name_to_crs(name: str) -> str:
    key = name.strip().lower()
    crs = STATION_CRS.get(key)
    if not crs:
        logger.warning(f"CRS code not found for station name: {name} (lookup key: {key})")
    return crs