import types

import pytest
from db.models.user import UserModel
from faker import Faker
from fastapi import status
from sqlalchemy import insert
from tests.conftest import db_service_base, initialize_database_base
from tests.factories.user_factory import UserFactory

from api.components.user.user_mapper import UserMapper
from api.components.user.user_models import User
from api.components.user.user_repository import UserRepository
from api.utils.dict_to_obj import DictToObj
from config.config import Config
from server_error import ServerError
from services.db_service import DBService


class TestUserRepository:
    @pytest.fixture(scope="class")
    def db_service(self) -> DBService:
        return db_service_base()

    @pytest.fixture
    def user_repository(self, db_service: DBService) -> UserRepository:
        return UserRepository(db_service)

    @pytest.fixture(scope="class", autouse=True)
    async def initialize_database(
        self, request, config: Config, db_service: DBService
    ) -> None:
        await initialize_database_base(request, config, db_service)


class TestCreateUser(TestUserRepository):
    def test_should_define_a_method(
        self,
        user_repository: UserRepository,
    ) -> None:
        assert isinstance(user_repository.create_user, types.MethodType) is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_user_when_user_is_created(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ):
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        mocked_user = UserMapper.to_domain(UserFactory.build())
        expected_result = UserMapper.to_domain(mocked_user)

        result = await user_repository.create_user(mocked_user)

        row_count = 1
        assert await db_service.get_database_table_row_count("users") == row_count
        assert result.id is not None
        assert result.name == expected_result.name
        assert result.email == expected_result.email
        assert result.created_at is not None
        assert result.updated_at is None
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_user_model_does_not_exist_into_database(
        self,
        user_repository: UserRepository,
    ):
        mocked_user = UserMapper.to_domain(UserFactory.build())
        message = "An error occurred when creating a user into database"
        server_error = ServerError(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(ServerError) as exc_info:
            await user_repository.create_user(mocked_user)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational


class TestReadAndCountUsers(TestUserRepository):
    def test_should_define_a_method(
        self,
        user_repository: UserRepository,
    ) -> None:
        assert (
            isinstance(user_repository.read_and_count_users, types.MethodType) is True
        )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_empty_list_of_users_with_zero_total_when_users_do_not_exist(
        self,
        db_service: DBService,
        user_repository: UserRepository,
        faker: Faker,
    ):
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        page = faker.pyint(min_value=1, max_value=3)
        limit = faker.pyint(min_value=1, max_value=3)
        expected_records = []
        expected_total = 0

        (
            records,
            total,
        ) = await user_repository.read_and_count_users(page, limit)

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert (records, total) == (
            expected_records,
            expected_total,
        )
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_list_of_users_with_non_zero_total_when_page_is_the_first_and_can_be_filled(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ):
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        count = 3
        mocked_user_list: list[User] = [
            UserMapper.to_domain(u) for u in UserFactory.build_batch(count)
        ]
        domain_user_list: list[User] = []
        for mocked_user in mocked_user_list:
            raw_user_data = UserMapper.to_persistence(mocked_user)
            async with db_service.async_engine.connect() as conn:
                query = insert(UserModel).values(raw_user_data).returning(UserModel)
                engine_result = await conn.execute(query)
                obj = DictToObj(engine_result.first()._asdict())
                await conn.commit()
                domain_user_list.append(UserMapper.to_domain(obj))
        page = 1
        limit = 1
        expected_records: list[User] = [domain_user_list[len(domain_user_list) - 1]]
        expected_total = count

        (
            records,
            total,
        ) = await user_repository.read_and_count_users(page, limit)

        row_count = count
        assert await db_service.get_database_table_row_count("users") == row_count
        assert records == expected_records
        assert total == expected_total
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_empty_list_of_users_with_non_zero_total_when_page_is_not_the_first_and_cannot_be_filled(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ):
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        count = 3
        mocked_user_list: list[User] = [
            UserMapper.to_domain(u) for u in UserFactory.build_batch(count)
        ]
        domain_user_list: list[User] = []
        for mocked_user in mocked_user_list:
            raw_user_data = UserMapper.to_persistence(mocked_user)
            async with db_service.async_engine.connect() as conn:
                query = insert(UserModel).values(raw_user_data).returning(UserModel)
                engine_result = await conn.execute(query)
                obj = DictToObj(engine_result.first()._asdict())
                await conn.commit()
                domain_user_list.append(UserMapper.to_domain(obj))
        page = 2
        limit = 3
        expected_records: list[User] = []
        expected_total = count

        (
            records,
            total,
        ) = await user_repository.read_and_count_users(page, limit)

        row_count = count
        assert await db_service.get_database_table_row_count("users") == row_count
        assert records == expected_records
        assert total == expected_total
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_list_of_users_with_non_zero_total_when_page_is_not_the_first_and_can_be_filled(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ):
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        count = 5
        mocked_user_list: list[User] = [
            UserMapper.to_domain(u) for u in UserFactory.build_batch(count)
        ]
        domain_user_list: list[User] = []
        for mocked_user in mocked_user_list:
            raw_user_data = UserMapper.to_persistence(mocked_user)
            async with db_service.async_engine.connect() as conn:
                query = insert(UserModel).values(raw_user_data).returning(UserModel)
                engine_result = await conn.execute(query)
                obj = DictToObj(engine_result.first()._asdict())
                await conn.commit()
                domain_user_list.append(UserMapper.to_domain(obj))
        page = 3
        limit = 2
        expected_records: list[User] = [domain_user_list[0]]
        expected_total = count

        (
            records,
            total,
        ) = await user_repository.read_and_count_users(page, limit)

        row_count = count
        assert await db_service.get_database_table_row_count("users") == row_count
        assert records == expected_records
        assert total == expected_total
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_user_model_does_not_exist_into_database(
        self,
        user_repository: UserRepository,
        faker: Faker,
    ):
        page = faker.pyint(min_value=1, max_value=3)
        limit = faker.pyint(min_value=1, max_value=3)
        message = "An error occurred when reading and counting users from database"
        server_error = ServerError(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(ServerError) as exc_info:
            await user_repository.read_and_count_users(page, limit)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational


class TestReadUser(TestUserRepository):
    def test_should_define_a_method(
        self,
        user_repository: UserRepository,
    ) -> None:
        assert isinstance(user_repository.read_user, types.MethodType) is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_user_when_user_is_read(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ) -> None:
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        raw_user_data = UserMapper.to_persistence(mocked_user)
        domain_user: User
        async with db_service.async_engine.connect() as conn:
            query = insert(UserModel).values(raw_user_data).returning(UserModel)
            engine_result = await conn.execute(query)
            obj = DictToObj(engine_result.first()._asdict())
            await conn.commit()
            domain_user = UserMapper.to_domain(obj)
        expected_result = domain_user

        result = await user_repository.read_user(domain_user.id)

        row_count = 1
        assert await db_service.get_database_table_row_count("users") == row_count
        assert result == expected_result
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_none_when_user_is_not_found(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ) -> None:
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        mocked_user: User = UserMapper.to_domain(UserFactory.build())

        result = await user_repository.read_user(mocked_user.id)

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert result is None
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_user_model_does_not_exist_into_database(
        self,
        user_repository: UserRepository,
    ):
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        message = "An error occurred when reading a user from database"
        server_error = ServerError(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(ServerError) as exc_info:
            await user_repository.read_user(mocked_user.id)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational


class TestUpdateUser(TestUserRepository):
    def test_should_define_a_method(
        self,
        user_repository: UserRepository,
    ) -> None:
        assert isinstance(user_repository.update_user, types.MethodType) is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_user_when_user_is_updated(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ):
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        raw_user_data = UserMapper.to_persistence(mocked_user)
        domain_user: User
        async with db_service.async_engine.connect() as conn:
            query = insert(UserModel).values(raw_user_data).returning(UserModel)
            engine_result = await conn.execute(query)
            obj = DictToObj(engine_result.first()._asdict())
            await conn.commit()
            domain_user: User = UserMapper.to_domain(
                UserFactory.build(id=obj.id, created_at=obj.created_at)
            )
        expected_result = domain_user

        result = await user_repository.update_user(domain_user.id, domain_user)

        row_count = 1
        assert await db_service.get_database_table_row_count("users") == row_count
        assert result.id == expected_result.id
        assert result.name == expected_result.name
        assert result.email == expected_result.email
        assert result.created_at == expected_result.created_at
        assert result.updated_at is not None
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_none_when_user_is_not_found(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ):
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        mocked_user: User = UserMapper.to_domain(UserFactory.build())

        result = await user_repository.update_user(mocked_user.id, mocked_user)

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert result is None
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_user_model_does_not_exist_into_database(
        self,
        user_repository: UserRepository,
    ):
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        message = "An error occurred when updating a user from database"
        server_error = ServerError(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(ServerError) as exc_info:
            await user_repository.update_user(mocked_user.id, mocked_user)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational


class TestDeleteUser(TestUserRepository):
    def test_should_define_a_method(
        self,
        user_repository: UserRepository,
    ) -> None:
        assert isinstance(user_repository.delete_user, types.MethodType) is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_user_when_user_is_deleted(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ):
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        raw_user_data = UserMapper.to_persistence(mocked_user)
        domain_user: User
        async with db_service.async_engine.connect() as conn:
            query = insert(UserModel).values(raw_user_data).returning(UserModel)
            engine_result = await conn.execute(query)
            obj = DictToObj(engine_result.first()._asdict())
            await conn.commit()
            domain_user = UserMapper.to_domain(obj)
        mocked_user.id = domain_user.id
        expected_result = domain_user

        result = await user_repository.delete_user(mocked_user.id)

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert result == expected_result
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_none_when_user_is_not_found(
        self,
        db_service: DBService,
        user_repository: UserRepository,
    ):
        alembic_file_path = "alembic.ini"
        await db_service.migrate_database(alembic_file_path)
        mocked_user: User = UserMapper.to_domain(UserFactory.build())

        result = await user_repository.delete_user(mocked_user.id)

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert result is None
        await db_service.delete_database_tables()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_raise_exception_when_user_model_does_not_exist_into_database(
        self,
        user_repository: UserRepository,
    ):
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        message = "An error occurred when deleting a user from database"
        server_error = ServerError(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(ServerError) as exc_info:
            await user_repository.delete_user(mocked_user.id)

        assert exc_info.value.message == server_error.message
        assert exc_info.value.status_code == server_error.status_code
        assert exc_info.value.is_operational == server_error.is_operational
