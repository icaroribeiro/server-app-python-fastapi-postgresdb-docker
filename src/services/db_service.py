from abc import ABC, abstractmethod

from alembic import command as alembic_command
from alembic import config as alembic_config
from fastapi import status
from sqlalchemy import Connection, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from logger.logger import logger
from server_error import Detail, ServerError


class IDBService(ABC):
    @abstractmethod
    async def connect_database(self, database_url: str) -> None:
        raise Exception("NotImplementedException")

    @abstractmethod
    async def check_database_is_alive(self) -> bool:
        raise Exception("NotImplementedException")

    @abstractmethod
    def migrate_database(self) -> None:
        raise Exception("NotImplementedException")

    @abstractmethod
    async def get_database_table_row_count(self, table_name: str) -> int:
        raise Exception("NotImplementedException")

    @abstractmethod
    async def clear_database_tables(self) -> None:
        raise Exception("NotImplementedException")

    @abstractmethod
    async def delete_database_tables(self) -> None:
        raise Exception("NotImplementedException")

    @abstractmethod
    async def disconnect_database(self) -> None:
        raise Exception("NotImplementedException")


class DBService(IDBService):
    __async_engine: AsyncEngine | None

    def __init__(self):
        self.__async_engine = None

    @property
    def async_engine(self) -> AsyncEngine:
        if self.__async_engine is not None:
            return self.__async_engine
        message = "Async engine is None!"
        logger.error(message)
        raise ServerError(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def connect_database(self, database_url: str) -> None:
        try:
            self.__async_engine = create_async_engine(
                url=database_url,
            )
        except Exception as err:
            message = "An error occurred when connecting to database"
            logger.error(message, err)
            raise ServerError(
                message,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                Detail(context=database_url, cause=str(err.__cause__)),
            )

    async def check_database_is_alive(self) -> bool:
        async with self.__async_engine.connect() as conn:
            try:
                query = text("""
                        SELECT 1
                    """)
                await conn.execute(query)
                await conn.commit()
                return True
            except Exception as err:
                message = "An error occurred when checking database is alive"
                logger.error(message, err)
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(context=None, cause=str(err.__cause__)),
                )

    async def migrate_database(self, alembic_file_path: str) -> None:
        async with self.__async_engine.connect() as conn:
            try:
                await conn.run_sync(self.__run_upgrade, alembic_file_path)
            except Exception as err:
                message = "An error occurred when migrating the database"
                logger.error(message, err)
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(context=alembic_file_path, cause=str(err.__cause__)),
                )

    async def get_database_table_row_count(self, table_name: str) -> int:
        async with self.__async_engine.connect() as conn:
            try:
                query = text(f"""
                        SELECT count(*)
                        FROM {table_name};
                    """)
                result = await conn.execute(query)
                _tuple = result.first()
                await conn.commit()
                return _tuple[0]
            except Exception as err:
                message = f"An error occurred when counting rows of database table {table_name}"
                logger.error(message, err)
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(context=table_name, cause=str(err.__cause__)),
                )

    async def clear_database_tables(self) -> None:
        async with self.__async_engine.connect() as conn:
            try:
                query = text("""
                        SELECT table_name
                        FROM information_schema.tables
                            WHERE table_schema = 'public'
                                AND table_type = 'BASE TABLE';
                    """)
                result = await conn.execute(query)
                for _tuple in result.fetchall():
                    table = _tuple[0]
                    query = text(f"TRUNCATE TABLE {table} CASCADE;")
                    await conn.execute(query)
                await conn.commit()
            except Exception as err:
                message = "An error occurred when cleaning the database tables"
                logger.error(message, err)
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(context=None, cause=str(err.__cause__)),
                )

    async def delete_database_tables(self) -> None:
        async with self.__async_engine.connect() as conn:
            try:
                query = text("""
                    SELECT table_name
                    FROM information_schema.tables
                        WHERE table_schema = 'public'
                            AND table_type = 'BASE TABLE';
                """)
                result = await conn.execute(query)
                for _tuple in result.fetchall():
                    table = _tuple[0]
                    query = text(f"DROP TABLE {table} CASCADE;")
                    await conn.execute(query)
                await conn.commit()
            except Exception as err:
                message = "An error occurred when deleting the database tables"
                logger.error(message, err)
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(context=None, cause=str(err.__cause__)),
                )

    async def disconnect_database(self) -> None:
        try:
            await self.__async_engine.dispose()
            self.__async_engine = None
        except Exception as err:
            message = "An error occurred when disconnecting the database"
            logger.error(message, err)
            raise ServerError(
                message,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                Detail(context=None, cause=str(err.__cause__)),
            )

    @staticmethod
    def __run_upgrade(conn: Connection, alembic_file_path: str):
        cfg = alembic_config.Config(alembic_file_path)
        cfg.attributes["connection"] = conn
        alembic_command.upgrade(cfg, "head")
