from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.national_rail import get_arrivals, get_departures
from models.TrainService import TrainService
import os
from dotenv import load_dotenv
import logging
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="Train Platform Crawler API",
    description="API for querying UK National Rail arrivals and departures, with platform and operator info.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logger = logging.getLogger("train-platform-crawler")

class StationRequest(BaseModel):
    crs_code: str

@app.get("/station/{crs_code}/arrivals", response_model=list[TrainService], tags=["Arrivals"], summary="Get arrivals for a station", description="Returns the last 5 arrivals for a given CRS code.")
def arrivals(crs_code: str):
    try:
        logger.info(f"Fetching arrivals for CRS: {crs_code}")
        return get_arrivals(crs_code)
    except Exception as e:
        logger.error(f"Error fetching arrivals for {crs_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.get("/station/{crs_code}/departures", response_model=list[TrainService], tags=["Departures"], summary="Get departures for a station", description="Returns the next 5 departures for a given CRS code.")
def departures(crs_code: str):
    try:
        logger.info(f"Fetching departures for CRS: {crs_code}")
        return get_departures(crs_code)
    except Exception as e:
        logger.error(f"Error fetching departures for {crs_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/station/arrivals", response_model=list[TrainService], tags=["Arrivals"], summary="Get arrivals via POST", description="Returns the last 5 arrivals for a given CRS code via POST request.")
def arrivals_post(request: StationRequest):
    try:
        logger.info(f"Fetching arrivals for CRS: {request.crs_code}")
        return get_arrivals(request.crs_code)
    except Exception as e:
        logger.error(f"Error fetching arrivals for {request.crs_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/station/departures", response_model=list[TrainService], tags=["Departures"], summary="Get departures via POST", description="Returns the next 5 departures for a given CRS code via POST request.")
def departures_post(request: StationRequest):
    try:
        logger.info(f"Fetching departures for CRS: {request.crs_code}")
        return get_departures(request.crs_code)
    except Exception as e:
        logger.error(f"Error fetching departures for {request.crs_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.get("/health", tags=["Health"], summary="Health check", description="Returns API health status.")
def health():
    return {"status": "ok"}
