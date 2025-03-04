import types

import pytest

from api.components.health_check.health_check_mapper import HealthCheckMapper
from api.components.health_check.health_check_models import HealthCheckResponse


class TestHealthCheckMapper:
    @pytest.fixture
    def health_check_mapper(self) -> HealthCheckMapper:
        return HealthCheckMapper()


class TestToResponse(TestHealthCheckMapper):
    def test_should_define_a_function(
        self,
        health_check_mapper: HealthCheckMapper,
    ) -> None:
        assert isinstance(health_check_mapper.to_response, types.FunctionType) is True

    def test_should_succeed_and_return_health_check_response(
        self,
        health_check_mapper: HealthCheckMapper,
    ) -> None:
        is_healthy = True
        health_check_response = HealthCheckResponse(healthy=is_healthy)
        expected_result = health_check_response

        result = health_check_mapper.to_response(is_healthy)

        assert result == expected_result
