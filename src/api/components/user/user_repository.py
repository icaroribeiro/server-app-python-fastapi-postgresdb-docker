from abc import ABC, abstractmethod
from uuid import UUID

from db.models.user import UserModel
from fastapi import status
from sqlalchemy import delete, desc, func, insert, select, update

from api.components.user.user_mapper import UserMapper
from api.components.user.user_models import User
from api.utils.dict_to_obj import DictToObj
from logger.logger import logger
from server_error import Detail, ServerError
from services.db_service import DBService


class IUserRepository(ABC):
    @abstractmethod
    async def create_user(self, user: User) -> User:
        raise Exception("NotImplementedException")

    @abstractmethod
    async def read_and_count_users(
        self, page: int, limit: int
    ) -> tuple[list[User], int]:
        raise Exception("NotImplementedException")

    @abstractmethod
    async def read_user(self, user_id: str) -> User | None:
        raise Exception("NotImplementedException")

    @abstractmethod
    async def update_user(self, user_id: str, user: User) -> User | None:
        raise Exception("NotImplementedException")

    @abstractmethod
    async def delete_user(self, user_id: str) -> User | None:
        raise Exception("NotImplementedException")


class UserRepository(IUserRepository):
    def __init__(self, db_service: DBService):
        self.db_service = db_service

    async def create_user(self, user: User) -> User:
        async with self.db_service.async_engine.connect() as conn:
            try:
                raw_user_data = UserMapper.to_persistence(user)
                query = insert(UserModel).values(raw_user_data).returning(UserModel)
                result = await conn.execute(query)
                obj = DictToObj(result.first()._asdict())
                await conn.commit()
                return UserMapper.to_domain(obj)
            except Exception as err:
                message = "An error occurred when creating a user into database"
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(context=user, cause=str(err.__cause__)),
                )

    async def read_and_count_users(
        self, page: int, limit: int
    ) -> tuple[list[User], int]:
        async with self.db_service.async_engine.connect() as conn:
            try:
                subquery = (
                    select(UserModel.id)
                    .order_by(desc(UserModel.created_at))
                    .limit(limit)
                    .offset((page - 1) * limit)
                    .subquery()
                )
                query = (
                    select(UserModel)
                    .join(
                        subquery,
                        UserModel.id == subquery.c.id,
                    )
                    .order_by(desc(UserModel.created_at))
                )
                result = await conn.execute(query)

                records: list[User] = []
                for record in result.all():
                    obj = DictToObj(record._asdict())
                    records.append(UserMapper.to_domain(obj))

                query = select(func.count(UserModel.id).label("count"))
                result = await conn.execute(query)
                obj = DictToObj(result.first()._asdict())
                total = obj.count
                await conn.commit()

                return records, total
            except Exception as err:
                message = (
                    "An error occurred when reading and counting users from database"
                )
                logger.error(message, err)
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(
                        context={"page": page, "limit": limit},
                        cause=str(err.__cause__),
                    ),
                )

    async def read_user(self, user_id: str) -> User | None:
        async with self.db_service.async_engine.connect() as conn:
            try:
                query = select(UserModel).where(UserModel.id == UUID(user_id))
                result = await conn.execute(query)
                if result.rowcount == 0:
                    return None
                obj = DictToObj(result.first()._asdict())
                await conn.commit()
                return UserMapper.to_domain(obj)
            except Exception as err:
                message = "An error occurred when reading a user from database"
                logger.error(message, err)
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(context=user_id, cause=str(err.__cause__)),
                )

    async def update_user(self, user_id: str, user: User) -> User | None:
        async with self.db_service.async_engine.connect() as conn:
            try:
                query = (
                    update(UserModel)
                    .where(UserModel.id == UUID(user_id))
                    .values(name=user.name, email=user.email)
                    .returning(UserModel)
                )
                result = await conn.execute(query)
                if result.rowcount == 0:
                    return None
                obj = DictToObj(result.first()._asdict())
                await conn.commit()
                return UserMapper.to_domain(obj)
            except Exception as err:
                message = "An error occurred when updating a user from database"
                logger.error(message, err)
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(
                        context={"user_id": user_id, "user": user},
                        cause=str(err.__cause__),
                    ),
                )

    async def delete_user(self, user_id: str) -> User | None:
        async with self.db_service.async_engine.connect() as conn:
            try:
                query = (
                    delete(UserModel)
                    .where(UserModel.id == UUID(user_id))
                    .returning(UserModel)
                )
                result = await conn.execute(query)
                if result.rowcount == 0:
                    return None
                obj = DictToObj(result.first()._asdict())
                await conn.commit()
                return UserMapper.to_domain(obj)
            except Exception as err:
                message = "An error occurred when deleting a user from database"
                logger.error(message, err)
                await conn.rollback()
                raise ServerError(
                    message,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    Detail(context=user_id, cause=str(err.__cause__)),
                )
