import asyncio
import re

import pytest
from db.models.user import UserModel
from faker import Faker
from fastapi import status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from sqlalchemy import insert
from tests.conftest import (
    db_service_base,
    delete_database_tables_base,
    initialize_database_base,
    migrate_database_base,
)
from tests.factories.user_factory import UserFactory

from api.components.user.user_mapper import UserMapper
from api.components.user.user_models import User, UserResponse
from api.shared.api_error_response import APIErrorResponse
from api.shared.api_pagination_response import APIPaginationResponse
from api.utils.dict_to_obj import DictToObj
from config.config import Config
from services.db_service import DBService


class TestUserHttp:
    @pytest.fixture(scope="class")
    def db_service(self) -> DBService:
        return db_service_base()

    @pytest.fixture
    def url(self, config: Config) -> str:
        endpoint = "/users"
        return f"http://localhost:{config.get_port()}{endpoint}"

    @pytest.fixture(scope="class", autouse=True)
    async def setup_and_teardown(
        self, request, config: Config, db_service: DBService
    ) -> None:
        await initialize_database_base(request, config, db_service)
        await migrate_database_base(db_service)

        def finalize():
            async def finalize_database() -> None:
                await delete_database_tables_base(db_service)

            asyncio.get_event_loop().run_until_complete(finalize_database())

        request.addfinalizer(finalize)


class TestAddUser(TestUserHttp):
    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_201_status_code_when_user_is_added(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        user_request = {"name": mocked_user.name, "email": mocked_user.email}
        expected_response_body = DictToObj(user_request)

        response = await async_client.post(url, json=user_request)

        row_count = 1
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_201_CREATED
        response_body: UserResponse = DictToObj(response.json())
        assert response_body.name == expected_response_body.name
        assert response_body.email == expected_response_body.email

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_return_422_status_code_when_user_request_email_is_invalid(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
        faker: Faker,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build(email=faker.word()))
        user_request = {"name": mocked_user.name, "email": mocked_user.email}

        response = await async_client.post(url, json=user_request)

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body: APIErrorResponse = DictToObj(response.json())
        assert response_body.is_operational is True


class TestFetchPaginatedUsers(TestUserHttp):
    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_200_status_code_with_empty_list_of_users_with_zero_total_when_users_do_not_exist(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
        base_url = url
        expected_response_body = APIPaginationResponse(
            page=1, limit=1, total_pages=0, total_records=0, records=[]
        )

        response = await async_client.get(base_url)

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == jsonable_encoder(expected_response_body)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_200_status_code_with_list_of_users_with_non_zero_total_when_page_is_the_first_and_can_be_filled(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
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
        base_url = f"{url}?page={page}&limit={limit}"
        next = re.sub(r"(page=)[^&]", rf"\g<1>{page+1}", base_url)
        expected_response_body = APIPaginationResponse(
            page=1,
            limit=1,
            total_pages=3,
            total_records=3,
            records=[UserMapper.to_response(domain_user_list[-1:][0])],
            next=next,
        )

        response = await async_client.get(base_url)

        row_count = 3
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == jsonable_encoder(expected_response_body)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_200_status_code_with_list_of_users_with_non_zero_total_when_page_is_not_the_first_and_cannot_be_filled(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
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
        base_url = f"{url}?page={page}&limit={limit}"
        expected_response_body = APIPaginationResponse(
            page=2,
            limit=3,
            total_pages=1,
            total_records=3,
            records=[],
        )

        response = await async_client.get(base_url)

        row_count = 3
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == jsonable_encoder(expected_response_body)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_200_status_code_with_list_of_users_with_non_zero_total_when_page_is_not_the_first_and_can_be_filled(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
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
        base_url = f"{url}?page={page}&limit={limit}"
        previous = re.sub(r"(page=)[^&]", rf"\g<1>{page-1}", base_url)
        expected_response_body = APIPaginationResponse(
            page=3,
            limit=2,
            total_pages=3,
            total_records=5,
            records=[UserMapper.to_response(domain_user_list[0])],
            previous=previous,
        )

        response = await async_client.get(f"{base_url}")

        row_count = 5
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == jsonable_encoder(expected_response_body)


class TestFetchUser(TestUserHttp):
    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_200_status_code_when_user_is_fetched(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        raw_user_data = UserMapper.to_persistence((mocked_user))
        domain_user: User
        async with db_service.async_engine.connect() as conn:
            query = insert(UserModel).values(raw_user_data).returning(UserModel)
            engine_result = await conn.execute(query)
            obj = DictToObj(engine_result.first()._asdict())
            await conn.commit()
            domain_user = UserMapper.to_domain(obj)
        expected_response_body = UserMapper.to_response(domain_user)

        response = await async_client.get(f"{url}/{domain_user.id}")

        row_count = 1
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == jsonable_encoder(expected_response_body)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_return_404_status_code_when_user_is_not_found(
        self,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())

        response = await async_client.get(f"{url}/{mocked_user.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_body: APIErrorResponse = DictToObj(response.json())
        assert response_body.is_operational is True


class TestRenewUser(TestUserHttp):
    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_200_status_code_when_user_is_renewed(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
        mocked_user = UserMapper.to_domain(UserFactory.build())
        raw_user_data = UserMapper.to_persistence(mocked_user)
        domain_user: User
        async with db_service.async_engine.connect() as conn:
            query = insert(UserModel).values(raw_user_data).returning(UserModel)
            engine_result = await conn.execute(query)
            obj = DictToObj(engine_result.first()._asdict())
            await conn.commit()
            domain_user = UserMapper.to_domain(obj)
        mocked_updated_user: UserModel = UserFactory.build(
            id=domain_user.id, created_at=domain_user.created_at
        )
        user_request = {
            "name": mocked_updated_user.name,
            "email": mocked_updated_user.email,
        }
        expected_response = DictToObj(user_request)

        response = await async_client.put(f"{url}/{domain_user.id}", json=user_request)

        row_count = 1
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_200_OK
        response_body: UserResponse = DictToObj(response.json())
        assert response_body.id == domain_user.id
        assert response_body.name == expected_response.name
        assert response_body.email == expected_response.email
        assert response_body.created_at == domain_user.created_at.isoformat()
        assert response_body.updated_at is not None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_return_404_status_code_when_user_is_not_found(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        user_request = {
            "name": mocked_user.name,
            "email": mocked_user.email,
        }

        response = await async_client.put(f"{url}/{mocked_user.id}", json=user_request)

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_body: APIErrorResponse = DictToObj(response.json())
        assert response_body.is_operational is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_return_422_status_code_when_user_request_email_is_invalid(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
        faker: Faker,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build(email=faker.word()))
        user_request = {
            "name": mocked_user.name,
            "email": mocked_user.email,
        }

        response = await async_client.put(f"{url}/{mocked_user.id}", json=user_request)

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body: APIErrorResponse = DictToObj(response.json())
        assert response_body.is_operational is True


class TestDestroyUser(TestUserHttp):
    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_succeed_and_return_200_status_code_when_user_is_destroyed(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        raw_user_data = UserMapper.to_persistence(mocked_user)
        domain_user: User
        async with db_service.async_engine.connect() as conn:
            query = insert(UserModel).values(raw_user_data).returning(UserModel)
            engine_result = await conn.execute(query)
            obj = DictToObj(engine_result.first()._asdict())
            await conn.commit()
            domain_user = UserMapper.to_domain(obj)
        expected_response_body = UserMapper.to_response(domain_user)

        response = await async_client.delete(f"{url}/{domain_user.id}")

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == jsonable_encoder(expected_response_body)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_should_fail_and_return_404_status_code_when_user_is_not_found(
        self,
        db_service: DBService,
        clear_database_tables: None,
        async_client: AsyncClient,
        url: str,
    ) -> None:
        mocked_user: UserModel = UserFactory.build()

        response = await async_client.delete(f"{url}/{mocked_user.id}")

        row_count = 0
        assert await db_service.get_database_table_row_count("users") == row_count
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_body: APIErrorResponse = DictToObj(response.json())
        assert response_body.is_operational is True
