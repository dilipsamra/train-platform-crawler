from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.national_rail import get_arrivals, get_departures
from models.TrainService import TrainService
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/station/{crs_code}/arrivals", response_model=list[TrainService])
def arrivals(crs_code: str):
    try:
        return get_arrivals(crs_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/station/{crs_code}/departures", response_model=list[TrainService])
def departures(crs_code: str):
    try:
        return get_departures(crs_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
