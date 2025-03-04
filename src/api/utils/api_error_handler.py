from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.shared.api_error_response import APIErrorResponse
from server_error import Detail, ServerError


class APIErrorHandler:
    def handle_request_validation_error(
        self, request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            content=APIErrorResponse(
                message="Validation failed",
                detail=Detail(context=error.body, cause=error.errors()),
                is_operational=True,
            ).model_dump(),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def handle_server_error(self, request: Request, error: ServerError) -> JSONResponse:
        return JSONResponse(
            content=APIErrorResponse(
                message=error.message,
                detail=error.detail,
                is_operational=error.is_operational,
            ).model_dump(),
            status_code=error.status_code,
        )

    def handle_common_error(self, request: Request, error: Exception) -> JSONResponse:
        return JSONResponse(
            content=APIErrorResponse(
                message=error.args[0],
                detail=Detail(context=None, cause=error),
                is_operational=False,
            ).model_dump(),
            status_code=error.status_code,
        )
