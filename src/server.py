from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from api.components.health_check import health_check_controller
from api.components.user import user_controller
from api.routers.routers import health_check_router, user_router
from api.utils.api_error_handler import APIErrorHandler
from config.config import Config
from container.container import Container
from server_error import ServerError


class Server:
    __app: FastAPI = FastAPI(
        title="Take-Home Assignment API",
        description="A REST API developed using Python and Postgres database\n\nSome useful links:\n- [The REST API repository](https://github.com/icaroribeiro/full-stack-app-with-reactjs-nodejs-python-docker)",  # noqa: E501
        version="1.0.0",
        openapi_url="/api-docs/swagger.json",
        docs_url="/api-docs",
        contact={
            "name": "Ícaro Ribeiro",
            "email": "icaroribeiro@hotmail.com",
            "url": "https://github.com/icaroribeiro",
        },
        license_info={
            "name": "MIT",
        },
        openapi_tags=[
            {"name": "health-check", "description": "Everything about health check"},
            {"name": "users", "description": "Everything about users"},
        ],
        servers=[
            {"url": "http://localhost:5001", "description": "Development environment"},
            {"url": "http://localhost:5000", "description": "Production environment"},
        ],
    )

    def __init__(self, config: Config):
        container = Container()
        db_service = container.db_service_provider()
        db_service.connect_database(config.get_database_url())
        container.wire(modules=[health_check_controller])
        container.wire(modules=[user_controller])
        self.__app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        api_error_handler = APIErrorHandler()
        exception_handlers = {
            RequestValidationError: api_error_handler.handle_request_validation_error,
            ServerError: api_error_handler.handle_server_error,
            Exception: api_error_handler.handle_common_error,
        }
        self.__app.exception_handlers = exception_handlers
        self.__app.include_router(router=health_check_router)
        self.__app.include_router(router=user_router)

    @property
    def app(self) -> FastAPI:
        return self.__app
