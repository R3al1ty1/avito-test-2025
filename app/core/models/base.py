from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from sqlalchemy import Column, Integer

from core.settings import settings


class Base(DeclarativeBase):
    __abstract__ = True

    metadata = MetaData(
        naming_convention=settings.db.naming_convention,
    )

    id = Column(Integer, primary_key=True, index=True)
