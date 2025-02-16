from sqlalchemy import Column, Integer, String, Text, ForeignKey

from .base import Base


class User(Base):
    __tablename__ = "users"

    username = Column(String(50), nullable=False, unique=True)
    password = Column(Text, nullable=False)
    balance = Column(Integer, nullable=False, default=0)


class UserItem(Base):
    __tablename__ = "user_items"

    name = Column(String(11), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)