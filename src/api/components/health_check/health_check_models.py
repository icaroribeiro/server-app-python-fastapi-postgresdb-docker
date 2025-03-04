from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    healthy: bool
