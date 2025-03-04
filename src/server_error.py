from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from api.shared.unknown_type import UnknownType

# from logger.logger import logger


class Detail(BaseModel):
    context: Optional[UnknownType] = None
    cause: Optional[UnknownType] = None


class ServerError(HTTPException):
    status_code: int
    is_operational: bool

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        detail: Optional[Detail] = None,
    ):
        super().__init__(status_code, detail)
        self.message = message
        if status_code:
            self.status_code = status_code
        else:
            self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.is_operational = True if f"{status_code}".startswith("4") else False
        # traceback.print_stack()
        # logger.info(repr(traceback.extract_stack()))
        # logger.info(repr(traceback.format_stack()))
