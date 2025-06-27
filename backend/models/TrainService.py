from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger("train-platform-crawler.models.TrainService")

class TrainService(BaseModel):
    scheduled_time: str
    expected_time: str
    platform: Optional[str] = None
    operator: Optional[str] = None
    destination: Optional[str] = None
    origin: Optional[str] = None
    service_id: Optional[str] = None
    status: Optional[str] = None
