import asyncio
from typing import AsyncGenerator

import pytest
from faker import Faker
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import DbContainer, PostgresContainer

from config.config import Config
from server import Server
from services.db_service import DBService


@pytest.fixture(scope="session")
def faker() -> Faker:
    return Faker()


@pytest.fixture(scope="session")
def config() -> Config:
    return Config()


def db_service_base() -> DBService:
    return DBService()


@pytest.fixture(scope="session", autouse=True)
def start_database_container(request, config: Config) -> DbContainer:
    db_user = config.get_database_username()
    db_password = config.get_database_password()
    db_name = config.get_database_name()
    container = PostgresContainer(
        image="postgres:latest",
        username=db_user,
        password=db_password,
        dbname=db_name,
        driver="asyncpg",
    ).start()
    db_url = container.get_connection_url()
    config.set_database_url(db_url)

    def stop_database_container() -> None:
        container.stop()

    request.addfinalizer(stop_database_container)
    return container


async def initialize_database_base(
    request, config: Config, db_service: DBService
) -> None:
    db_service.connect_database(config.get_database_url())

    def finalize():
        async def finalize_database() -> None:
            await db_service.disconnect_database()

        asyncio.get_event_loop().run_until_complete(finalize_database())

    request.addfinalizer(finalize)


async def migrate_database_base(db_service: DBService) -> None:
    alembic_file_path = "alembic.ini"
    await db_service.migrate_database(alembic_file_path)


@pytest.fixture
async def clear_database_tables(db_service: DBService) -> None:
    await db_service.clear_database_tables()


async def delete_database_tables_base(db_service: DBService) -> None:
    await db_service.delete_database_tables()


@pytest.fixture(scope="session")
async def async_client(config: Config) -> AsyncGenerator[AsyncClient, None]:
    server = Server(config)
    async with AsyncClient(transport=ASGITransport(app=server.app)) as async_client:
        yield async_client
