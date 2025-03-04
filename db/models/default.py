import uuid
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

class Default:
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )