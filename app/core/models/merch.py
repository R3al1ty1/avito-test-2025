from sqlalchemy import Column, Integer, String, Text

from .base import Base


class MerchItem(Base):
    __tablename__ = "merch_items"

    name = Column(String(11), nullable=False)
    price = Column(Integer, nullable=False)