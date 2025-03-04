import pytest

from api.components.health_check.health_check_service import HealthCheckService
from api.components.user.user_repository import UserRepository
from api.components.user.user_service import UserService
from container.container import Container
from services.api_pagination_service import APIPaginationService
from services.db_service import DBService


class TestContainer:
    @pytest.fixture
    def container(
        self,
    ) -> Container:
        return Container()

    def test_should_succeed_when_checking_injection_of_dependencies(
        self, container: Container
    ) -> None:
        providers_by_name = {
            "db_service_provider": container.db_service_provider,
            "user_repository_provider": container.user_repository_provider,
            "health_check_service_provider": container.health_check_service_provider,
            "user_service_provider": container.user_service_provider,
            "api_pagination_service_provider": container.api_pagination_service_provider,
        }
        assert container.providers == providers_by_name
        assert isinstance(providers_by_name["db_service_provider"](), DBService) is True
        assert (
            isinstance(providers_by_name["user_repository_provider"](), UserRepository)
            is True
        )
        assert (
            isinstance(
                providers_by_name["health_check_service_provider"](),
                HealthCheckService,
            )
            is True
        )
        assert (
            isinstance(providers_by_name["user_service_provider"](), UserService)
            is True
        )
        assert (
            isinstance(
                providers_by_name["api_pagination_service_provider"](),
                APIPaginationService,
            )
            is True
        )
