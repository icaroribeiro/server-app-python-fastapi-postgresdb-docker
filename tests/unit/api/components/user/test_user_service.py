import types

import pytest
from db.models.user import UserModel
from faker import Faker
from fastapi import status
from pytest_mock import MockerFixture
from tests.conftest import db_service_base
from tests.factories.user_factory import UserFactory

from api.components.user.user_mapper import UserMapper
from api.components.user.user_models import User
from api.components.user.user_repository import UserRepository
from api.components.user.user_service import UserService
from server_error import ServerError
from services.db_service import DBService


class TestUserService:
    @pytest.fixture(scope="class")
    def db_service(self) -> DBService:
        return db_service_base()

    @pytest.fixture(scope="class")
    def user_repository(
        self,
        db_service: DBService,
    ) -> UserRepository:
        return UserRepository(db_service)

    @pytest.fixture
    def user_service(
        self,
        user_repository: UserRepository,
    ) -> UserService:
        return UserService(user_repository)


class TestRegisterUser(TestUserService):
    def test_should_define_a_method(
        self,
        user_service: UserService,
    ) -> None:
        assert isinstance(user_service.register_user, types.MethodType) is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_user_when_user_is_registered(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        mocked_create_user = mocker.AsyncMock(return_value=mocked_user)
        user_repository.create_user = mocked_create_user
        expected_result = mocked_user

        result = await user_service.register_user(mocked_user)

        assert result == expected_result
        user_repository.create_user.assert_called_once_with(mocked_user)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_an_error_occurred_when_creating_a_user(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        error = Exception("failed")
        message = "An error occurred when creating a user"
        server_error = ServerError(message, status.HTTP_500_INTERNAL_SERVER_ERROR)
        mocked_create_user = mocker.AsyncMock(side_effect=error)
        user_repository.create_user = mocked_create_user

        with pytest.raises(ServerError) as exc_info:
            await user_service.register_user(mocked_user)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.create_user.assert_called_once_with(mocked_user)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_user_could_not_be_created(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        message = "User could not be created"
        server_error = ServerError(message, status.HTTP_500_INTERNAL_SERVER_ERROR)
        mocked_create_user = mocker.AsyncMock(return_value=None)
        user_repository.create_user = mocked_create_user

        with pytest.raises(ServerError) as exc_info:
            await user_service.register_user(mocked_user)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.create_user.assert_called_once_with(mocked_user)


class TestRetrieveAndCountUsers(TestUserService):
    def test_should_define_a_method(
        self,
        user_service: UserService,
    ) -> None:
        assert (
            isinstance(user_service.retrieve_and_count_users, types.MethodType) is True
        )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_list_of_users_with_non_zero_total_when_users_exist(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
        faker: Faker,
    ) -> None:
        page = faker.pyint(min_value=1, max_value=3)
        limit = faker.pyint(min_value=1, max_value=3)
        count = faker.pyint(min_value=1, max_value=3)
        mocked_users: list[User] = [
            UserMapper.to_domain(u) for u in UserFactory.build_batch(count)
        ]
        mocked_read_and_count_users = mocker.AsyncMock(
            return_value=(mocked_users, count)
        )
        user_repository.read_and_count_users = mocked_read_and_count_users
        expected_result = (mocked_users, count)

        result = await user_service.retrieve_and_count_users(page, limit)

        assert result == expected_result
        user_repository.read_and_count_users.assert_called_once_with(page, limit)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_an_error_occurred_when_reading_and_counting_users(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
        faker: Faker,
    ) -> None:
        page = faker.pyint(min_value=1, max_value=3)
        limit = faker.pyint(min_value=1, max_value=3)
        error = Exception("failed")
        message = "An error occurred when reading and counting users"
        server_error = ServerError(
            message,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        mocked_read_and_count_users = mocker.AsyncMock(side_effect=error)
        user_repository.read_and_count_users = mocked_read_and_count_users

        with pytest.raises(ServerError) as exc_info:
            await user_service.retrieve_and_count_users(page, limit)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.read_and_count_users.assert_called_once_with(page, limit)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_users_could_not_be_read_and_counted(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
        faker: Faker,
    ) -> None:
        page = faker.pyint(min_value=1, max_value=3)
        limit = faker.pyint(min_value=1, max_value=3)
        message = "Users could not be read and counted"
        server_error = ServerError(
            message,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        mocked_read_and_count_users = mocker.AsyncMock(return_value=(None, None))
        user_repository.read_and_count_users = mocked_read_and_count_users

        with pytest.raises(ServerError) as exc_info:
            await user_service.retrieve_and_count_users(page, limit)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.read_and_count_users.assert_called_once_with(page, limit)


class TestRetrieveUser(TestUserService):
    def test_should_define_a_method(
        self,
        user_service: UserService,
    ) -> None:
        assert isinstance(user_service.retrieve_user, types.MethodType) is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_user_when_user_is_retrieved(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        mocked_read_user = mocker.AsyncMock(return_value=mocked_user)
        user_repository.read_user = mocked_read_user
        expected_result = mocked_user

        result = await user_service.retrieve_user(mocked_user.id)

        assert result == expected_result
        user_repository.read_user.assert_called_once_with(mocked_user.id)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_an_error_occurred_when_reading_a_user(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        error = Exception("failed")
        message = "An error occurred when reading a user"
        server_error = ServerError(
            message,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        mocked_read_user = mocker.Mock(side_effect=error)
        user_repository.read_user = mocked_read_user

        with pytest.raises(ServerError) as exc_info:
            await user_service.retrieve_user(mocked_user.id)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.read_user.assert_called_once_with(mocked_user.id)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_user_could_not_be_read(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        message = "User could not be read"
        server_error = ServerError(
            message,
            status.HTTP_404_NOT_FOUND,
        )
        mocked_read_user = mocker.AsyncMock(return_value=None)
        user_repository.read_user = mocked_read_user

        with pytest.raises(ServerError) as exc_info:
            await user_service.retrieve_user(mocked_user.id)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.read_user.assert_called_once_with(mocked_user.id)


class TestReplaceUser(TestUserService):
    def test_should_define_a_method(
        self,
        user_service: UserService,
    ) -> None:
        assert isinstance(user_service.replace_user, types.MethodType) is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_user_when_user_is_replaced(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        mocked_update_user = mocker.AsyncMock(return_value=mocked_user)
        user_repository.update_user = mocked_update_user
        expected_result = mocked_user

        result = await user_service.replace_user(mocked_user.id, mocked_user)

        assert result == expected_result
        user_repository.update_user.assert_called_once_with(mocked_user.id, mocked_user)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_an_error_occurred_when_updating_a_user(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        error = Exception("failed")
        message = "An error occurred when updating a user"
        server_error = ServerError(
            message,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        mocked_update_user = mocker.Mock(side_effect=error)
        user_repository.update_user = mocked_update_user

        with pytest.raises(ServerError) as exc_info:
            await user_service.replace_user(mocked_user.id, mocked_user)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.update_user.assert_called_once_with(mocked_user.id, mocked_user)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_user_could_not_be_updated(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        message = "User could not be updated"
        server_error = ServerError(
            message,
            status.HTTP_404_NOT_FOUND,
        )
        mocked_update_user = mocker.AsyncMock(return_value=None)
        user_repository.update_user = mocked_update_user

        with pytest.raises(ServerError) as exc_info:
            await user_service.replace_user(mocked_user.id, mocked_user)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.update_user.assert_called_once_with(mocked_user.id, mocked_user)


class TestRemoveUser(TestUserService):
    def test_should_define_a_method(
        self,
        user_service: UserService,
    ) -> None:
        assert isinstance(user_service.remove_user, types.MethodType) is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_user_when_user_is_removed(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: UserModel = UserFactory.build()
        mocked_delete_user = mocker.AsyncMock(return_value=mocked_user)
        user_repository.delete_user = mocked_delete_user
        expected_result = mocked_user

        result = await user_service.remove_user(mocked_user.id)

        assert result == expected_result
        user_repository.delete_user.assert_called_once_with(mocked_user.id)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_an_error_occurred_when_deleting_a_user(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        error = Exception("failed")
        message = "An error occurred when deleting a user"
        server_error = ServerError(
            message,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        mocked_delete_user = mocker.Mock(side_effect=error)
        user_repository.delete_user = mocked_delete_user

        with pytest.raises(ServerError) as exc_info:
            await user_service.remove_user(mocked_user.id)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.delete_user.assert_called_once_with(mocked_user.id)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_user_could_not_be_removed(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        mocker: MockerFixture,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        message = "User could not be removed"
        server_error = ServerError(
            message,
            status.HTTP_404_NOT_FOUND,
        )
        mocked_delete_user = mocker.AsyncMock(return_value=None)
        user_repository.delete_user = mocked_delete_user

        with pytest.raises(ServerError) as exc_info:
            await user_service.remove_user(mocked_user.id)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
        user_repository.delete_user.assert_called_once_with(mocked_user.id)
