import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator
from typing_extensions import Self


class UserRequest(BaseModel):
    name: str = Field(max_length=256)
    email: EmailStr

    @model_validator(mode="after")
    def validate(self) -> Self:
        return self


class User(BaseModel):
    id: str | None = None
    name: str
    email: str
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
