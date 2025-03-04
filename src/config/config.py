import os

from fastapi import status

from server_error import ServerError


class Config:
    def get_log_level(self) -> str:
        return self.__get_env_var("LOG_LEVEL")

    def get_env(self) -> str:
        return self.__get_env_var("ENV")

    def get_port(self) -> str:
        return self.__get_env_var("PORT")

    def get_database_url(self) -> str:
        return self.__get_env_var("DATABASE_URL")

    def get_database_username(self) -> str:
        return self.__get_env_var("DATABASE_USERNAME")

    def get_database_password(self) -> str:
        return self.__get_env_var("DATABASE_PASSWORD")

    def get_database_name(self) -> str:
        return self.__get_env_var("DATABASE_NAME")

    def get_database_port(self) -> str:
        return self.__get_env_var("DATABASE_PORT")

    def get_allowed_origins(self) -> str:
        return self.__get_env_var("ALLOWED_ORIGINS")

    @staticmethod
    def set_database_url(database_url: str) -> None:
        os.environ["DATABASE_URL"] = database_url

    @staticmethod
    def __get_env_var(name: str) -> str:
        if os.environ.get(name) is None:
            message = f"{name} environment variable isn't set!"
            raise ServerError(message, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return os.environ.get(name)
