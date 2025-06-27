from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models.TrainService import TrainService
from pydantic import BaseModel
from typing import Dict, Any

# Import new modules
from core.config import get_settings
from core.logging import setup_logging, get_logger
from core.exceptions import (
    global_exception_handler,
    TrainPlatformCrawlerException,
    create_http_exception
)
from services.train_service import get_train_service
from services.notifications.notification_service import get_notification_service
from services.notifications.base import NotificationType

# Initialize configuration and logging
settings = get_settings()
logger = setup_logging()

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Get service instances
train_service = get_train_service()
notification_service = get_notification_service()

class StationRequest(BaseModel):
    crs_code: str

@app.get("/station/{crs_code}/arrivals", response_model=list[TrainService], tags=["Arrivals"], summary="Get arrivals for a station", description="Returns the last 5 arrivals for a given CRS code.")
def arrivals(crs_code: str):
    try:
        logger.info(f"Fetching arrivals for CRS: {crs_code}")
        return train_service.get_arrivals(crs_code)
    except TrainPlatformCrawlerException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error fetching arrivals for {crs_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.get("/station/{crs_code}/departures", response_model=list[TrainService], tags=["Departures"], summary="Get departures for a station", description="Returns the next 5 departures for a given CRS code.")
def departures(crs_code: str):
    try:
        logger.info(f"Fetching departures for CRS: {crs_code}")
        return train_service.get_departures(crs_code)
    except TrainPlatformCrawlerException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error fetching departures for {crs_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/station/arrivals", response_model=list[TrainService], tags=["Arrivals"], summary="Get arrivals via POST", description="Returns the last 5 arrivals for a given CRS code via POST request.")
def arrivals_post(request: StationRequest):
    try:
        logger.info(f"Fetching arrivals for CRS: {request.crs_code}")
        return train_service.get_arrivals(request.crs_code)
    except TrainPlatformCrawlerException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error fetching arrivals for {request.crs_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/station/departures", response_model=list[TrainService], tags=["Departures"], summary="Get departures via POST", description="Returns the next 5 departures for a given CRS code via POST request.")
def departures_post(request: StationRequest):
    try:
        logger.info(f"Fetching departures for CRS: {request.crs_code}")
        return train_service.get_departures(request.crs_code)
    except TrainPlatformCrawlerException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error fetching departures for {request.crs_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

# New endpoints for enhanced functionality
class NotificationRequest(BaseModel):
    notification_type: str
    recipient: str
    station_name: str
    message: str

@app.get("/station/{crs_code}/status", tags=["Station Status"], summary="Get station status", description="Returns overall status information for a station including delays.")
def station_status(crs_code: str):
    try:
        logger.info(f"Fetching station status for CRS: {crs_code}")
        return train_service.get_station_status(crs_code)
    except TrainPlatformCrawlerException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error fetching station status for {crs_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.get("/notifications/status", tags=["Notifications"], summary="Get notification service status", description="Returns the status of all notification providers.")
def notification_status():
    try:
        return notification_service.get_notifier_status()
    except Exception as e:
        logger.error(f"Error getting notification status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/notifications/test", tags=["Notifications"], summary="Send test notification", description="Send a test notification via specified channel.")
def send_test_notification(request: NotificationRequest):
    try:
        from services.notifications.base import NotificationMessage, NotificationPriority
        
        # Validate notification type
        try:
            notification_type = NotificationType(request.notification_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid notification type: {request.notification_type}")
        
        # Create test message
        message = NotificationMessage(
            recipient=request.recipient,
            subject=f"Test Notification - {request.station_name}",
            body=request.message,
            notification_type=notification_type,
            priority=NotificationPriority.NORMAL,
            metadata={"test": True, "station_name": request.station_name}
        )
        
        # Send notification
        result = notification_service.send_notification(notification_type, message)
        
        return {
            "success": result.success,
            "message_id": result.message_id,
            "error": result.error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.get("/health", tags=["Health"], summary="Health check", description="Returns API health status.")
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment
    }
