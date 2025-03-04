from pydantic import BaseModel

from server_error import Detail


class APIErrorResponse(BaseModel):
    message: str
    detail: Detail | None = None
    is_operational: bool
