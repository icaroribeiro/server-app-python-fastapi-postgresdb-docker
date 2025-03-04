from abc import ABC, abstractmethod

from fastapi import status

from logger.logger import logger
from server_error import Detail, ServerError
from services.db_service import DBService


class IHealthCheckService(ABC):
    @abstractmethod
    async def check_health(self) -> bool:
        raise Exception("NotImplementedException")


class HealthCheckService(IHealthCheckService):
    def __init__(self, db_service: DBService):
        self.db_service = db_service

    async def check_health(self) -> bool:
        try:
            return await self.db_service.check_database_is_alive()
        except Exception as err:
            message = "An error occurred when checking if application is healthy"
            logger.error(message)
            raise ServerError(
                message,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                Detail(
                    context=None,
                    cause=str(err.detail.cause)
                    if isinstance(err, ServerError)
                    else str(err),
                ),
            )
