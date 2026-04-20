from datetime import datetime

from pydantic import BaseModel


class ApiInfo(BaseModel):
    name: str
    version: str
    docs_url: str
    health_url: str
    capabilities: list[str]


class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
