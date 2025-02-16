from sqlalchemy import Column, Integer, String, Text

from .base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    sender = Column(Integer, nullable=False)
    receiver = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)