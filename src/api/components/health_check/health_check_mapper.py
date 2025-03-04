from abc import ABC, abstractmethod

from api.components.health_check.health_check_models import HealthCheckResponse


class IHealthCheckMapper(ABC):
    @abstractmethod
    def to_response(is_healthy: bool) -> HealthCheckResponse:
        raise Exception("NotImplementedException")


class HealthCheckMapper(IHealthCheckMapper):
    @staticmethod
    def to_response(is_healthy: bool) -> HealthCheckResponse:
        return HealthCheckResponse(healthy=is_healthy)
