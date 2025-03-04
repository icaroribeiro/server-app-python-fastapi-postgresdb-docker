import types

import pytest
from fastapi import status
from pytest_mock import MockerFixture
from tests.conftest import db_service_base, initialize_database_base

from api.components.health_check.health_check_service import HealthCheckService
from config.config import Config
from server_error import Detail, ServerError
from services.db_service import DBService


class TestHealthCheckService:
    @pytest.fixture(scope="class")
    def db_service(self) -> DBService:
        return db_service_base()

    @pytest.fixture
    def health_check_service(
        self,
        db_service: DBService,
    ) -> HealthCheckService:
        return HealthCheckService(db_service)

    @pytest.fixture(scope="class", autouse=True)
    async def initialize_database(
        self, request, config: Config, db_service: DBService
    ) -> None:
        await initialize_database_base(request, config, db_service)


class TestCheckHealth(TestHealthCheckService):
    def test_should_define_a_method(
        self,
        health_check_service: HealthCheckService,
    ) -> None:
        assert isinstance(health_check_service.check_health, types.MethodType) is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_true_when_application_is_healthy(
        self,
        db_service: DBService,
        initialize_database: None,
        health_check_service: HealthCheckService,
        mocker: MockerFixture,
    ) -> None:
        mocked_check_database_is_alive = mocker.AsyncMock(return_value=True)
        db_service.check_database_is_alive = mocked_check_database_is_alive
        expected_result = True

        result = await health_check_service.check_health()

        assert result == expected_result
        db_service.check_database_is_alive.assert_called_once()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_application_is_not_healthy(
        self,
        db_service: DBService,
        health_check_service: HealthCheckService,
        mocker: MockerFixture,
    ) -> None:
        error = Exception("failed")
        message = "An error occurred when checking if application is healthy"
        server_error = ServerError(
            message,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            Detail(context=None, cause=error),
        )
        mocked_check_database_is_alive = mocker.Mock(side_effect=error)
        db_service.check_database_is_alive = mocked_check_database_is_alive

        with pytest.raises(ServerError) as exc_info:
            await health_check_service.check_health()

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        db_service.check_database_is_alive.assert_called_once()
