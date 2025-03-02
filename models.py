from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger, Date
from sqlalchemy.orm import relationship
from db import Base

class TelegramUsers(Base):
    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    telegram_username = Column(String, nullable=False)
    todos = relationship("TodoLists", back_populates="user", cascade="all, delete")

class TodoLists(Base):
    __tablename__ = "todo_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("telegram_users.id"), nullable=False)
    todo_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    deadline = Column(Date, nullable=True)
    is_done = Column(Boolean, default=False)

    user = relationship("TelegramUsers", back_populates="todos")
