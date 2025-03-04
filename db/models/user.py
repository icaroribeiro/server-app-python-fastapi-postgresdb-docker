from db.migrations.base import Base
from sqlalchemy import Column, DateTime, Integer, String, func

from db.models.default import Default

class UserModel(Default, Base):
    __tablename__ = "users"

    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)