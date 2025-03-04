from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request, Response, status

from api.components.user.user_mapper import UserMapper
from api.components.user.user_models import UserRequest, UserResponse
from api.components.user.user_service import UserService
from api.shared.api_error_response import APIErrorResponse
from api.shared.api_pagination_response import APIPaginationResponse
from container.container import Container
from services.api_pagination_service import APIPaginationData, APIPaginationService


class UserController(APIRouter):
    def __init__(
        self,
        prefix="/users",
        dependencies=[
            Depends(Provide[Container.user_service_provider]),
            Depends(Provide[Container.api_pagination_service_provider]),
        ],
    ):
        super().__init__(prefix=prefix, dependencies=dependencies)
        self.setup_routes()

    def setup_routes(self):
        @APIRouter.api_route(
            self,
            path="",
            methods=["POST"],
            tags=["users"],
            summary="""
             Add user
            """,
            description="""
             API endpoint used to create a new user.
            """,
            responses={
                status.HTTP_201_CREATED: {
                    "model": UserResponse,
                    "description": "Created",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                                "name": "name",
                                "email": "email@email.com",
                                "created_at": "XXXX-XX-XXTXX:XX:XX.XXXXXX",
                                "updated_at": "",
                            }
                        }
                    },
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY: {
                    "model": APIErrorResponse,
                    "description": "Unprocessable Entity",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "",
                                "detail": {"context": "", "cause": ""},
                                "isOperational": True,
                            }
                        }
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "model": APIErrorResponse,
                    "description": "Internal Server Error",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Internal Server Error",
                                "detail": {"context": "", "cause": ""},
                                "isOperational": False,
                            }
                        }
                    },
                },
            },
        )
        @inject
        async def add_user(
            response: Response,
            user_request: UserRequest,
            user_service: UserService = self.dependencies[0],
        ) -> UserResponse:
            domain_user = UserMapper.to_domain(user_request)
            returned_user = await user_service.register_user(domain_user)
            user_response = UserMapper.to_response(returned_user)
            response.status_code = status.HTTP_201_CREATED
            return user_response

        @APIRouter.api_route(
            self,
            path="",
            methods=["GET"],
            tags=["users"],
            summary="""
             Fetch paginated users
            """,
            description="""
             API endpoint used to get users through page-based pagination schema.
            """,
            responses={
                status.HTTP_200_OK: {
                    "model": UserResponse,
                    "description": "OK",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                                "name": "name",
                                "email": "email@email.com",
                                "created_at": "XXXX-XX-XXTXX:XX:XX.XXXXXX",
                                "updated_at": None,
                            }
                        }
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "model": APIErrorResponse,
                    "description": "Internal Server Error",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Internal Server Error",
                                "detail": {"context": "context", "cause": "cause"},
                                "isOperational": False,
                            }
                        }
                    },
                },
            },
        )
        @inject
        async def fetch_paginated_users(
            request: Request,
            response: Response,
            page: Annotated[
                int | None,
                Query(
                    description="The number of the page. If isn't provided, it will be set to 1."
                ),
            ] = 1,
            limit: Annotated[
                int | None,
                Query(
                    description="The number of records per page. If isn't provided, it will be set to 1."
                ),
            ] = 1,
            user_service: UserService = self.dependencies[0],
            api_pagination_service: APIPaginationService = self.dependencies[1],
        ) -> APIPaginationResponse:
            base_url = str(request.url)
            (
                records,
                total,
            ) = await user_service.retrieve_and_count_users(page, limit)
            api_pagination_data = APIPaginationData(
                page=page, limit=limit, records=records, total_records=total
            )
            api_pagination_response = api_pagination_service.create_response(
                base_url, api_pagination_data
            )
            response.status_code = status.HTTP_200_OK
            return api_pagination_response

        @APIRouter.api_route(
            self,
            path="/{user_id}",
            methods=["GET"],
            tags=["users"],
            summary="""
             Fetch user
            """,
            description="""
             API endpoint used to get a user by its ID.
            """,
            responses={
                status.HTTP_200_OK: {
                    "model": UserResponse,
                    "description": "OK",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                                "name": "name",
                                "email": "email@email.com",
                                "created_at": "XXXX-XX-XXTXX:XX:XX.XXXXXX",
                                "updated_at": None,
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {
                    "model": APIErrorResponse,
                    "description": "Not Found",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Not Found",
                                "detail": {"context": "context", "cause": "cause"},
                                "isOperational": True,
                            }
                        }
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "model": APIErrorResponse,
                    "description": "Internal Server Error",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Internal Server Error",
                                "detail": {"context": "context", "cause": "cause"},
                                "isOperational": False,
                            }
                        }
                    },
                },
            },
        )
        @inject
        async def fetch_user(
            response: Response,
            user_id: str,
            user_service: UserService = self.dependencies[0],
        ) -> UserResponse:
            retrieved_user = await user_service.retrieve_user(user_id)
            user_response = UserMapper.to_response(retrieved_user)
            response.status_code = status.HTTP_200_OK
            return user_response

        @APIRouter.api_route(
            self,
            path="/{user_id}",
            methods=["PUT"],
            tags=["users"],
            summary="""
             Renew user
            """,
            description="""
             API endpoint used to update a user by its ID.
            """,
            responses={
                status.HTTP_200_OK: {
                    "model": UserResponse,
                    "description": "OK",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                                "name": "name",
                                "email": "email@email.com",
                                "created_at": "XXXX-XX-XXTXX:XX:XX.XXXXXX",
                                "updated_at": None,
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {
                    "model": APIErrorResponse,
                    "description": "Not Found",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Not Found",
                                "detail": {"context": "context", "cause": ""},
                                "isOperational": True,
                            }
                        }
                    },
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY: {
                    "model": APIErrorResponse,
                    "description": "Unprocessable Entity",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Unprocessable Entity",
                                "detail": {"context": "context", "cause": "cause"},
                                "isOperational": True,
                            }
                        }
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "model": APIErrorResponse,
                    "description": "Internal Server Error",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Internal Server Error",
                                "detail": {"context": "context", "cause": "cause"},
                                "isOperational": False,
                            }
                        }
                    },
                },
            },
        )
        @inject
        async def renew_user(
            response: Response,
            user_id: str,
            user_request: UserRequest,
            user_service: UserService = self.dependencies[0],
        ) -> UserResponse:
            domain_user = UserMapper.to_domain(user_request)
            returned_user = await user_service.replace_user(user_id, domain_user)
            user_response = UserMapper.to_response(returned_user)
            response.status_code = status.HTTP_200_OK
            return user_response

        @APIRouter.api_route(
            self,
            path="/{user_id}",
            methods=["DELETE"],
            tags=["users"],
            summary="""
             Destroy user
            """,
            description="""
             API endpoint used to delete a user by its ID.
            """,
            responses={
                status.HTTP_200_OK: {
                    "model": UserResponse,
                    "description": "OK",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                                "name": "name",
                                "email": "email@email.com",
                                "created_at": "XXXX-XX-XXTXX:XX:XX.XXXXXX",
                                "updated_at": None,
                            }
                        }
                    },
                },
                status.HTTP_404_NOT_FOUND: {
                    "model": APIErrorResponse,
                    "description": "Not Found",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Not Found",
                                "detail": {"context": "context", "cause": "cause"},
                                "isOperational": True,
                            }
                        }
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "model": APIErrorResponse,
                    "description": "Internal Server Error",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Internal Server Error",
                                "detail": {"context": "context", "cause": "cause"},
                                "isOperational": False,
                            }
                        }
                    },
                },
            },
        )
        @inject
        async def destroy_user(
            response: Response,
            user_id: str,
            user_service: UserService = self.dependencies[0],
        ) -> UserResponse:
            returned_user = await user_service.remove_user(user_id)
            user_response = UserMapper.to_response(returned_user)
            response.status_code = status.HTTP_200_OK
            return user_response
