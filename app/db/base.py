# app/db/base.py (正确)
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass