from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger("train-platform-crawler.models.TrainService")

class TrainService(BaseModel):
    scheduled_time: str
    expected_time: str
    platform: Optional[str]
    operator: str
    destination: str
    origin: str
    service_id: str
    status: Optional[str]
