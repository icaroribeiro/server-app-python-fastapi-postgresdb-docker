import pytest
from fastapi import status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from api.components.health_check.health_check_models import HealthCheckResponse
from config.config import Config


class TestHealthCheckHttp:
    @pytest.fixture
    def url(self, config: Config) -> str:
        endpoint = "/health"
        return f"http://localhost:{config.get_port()}{endpoint}"


class TestGetHealth(TestHealthCheckHttp):
    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_200_status_code_when_application_is_heathy(
        self, async_client: AsyncClient, url: str
    ) -> None:
        expected_response_body = HealthCheckResponse(healthy=True)

        response = await async_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == jsonable_encoder(expected_response_body)
