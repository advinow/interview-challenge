from sqlalchemy import (
    Column, 
    Table, 
    Integer, 
    String, 
    DateTime, 
    Boolean,
    ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


association_table = Table(
    "business_symptom_m2m",
    Base.metadata,
    Column("business_id", ForeignKey("business.id"), primary_key=True),
    Column("symptom_code", ForeignKey("symptom.code"), primary_key=True),
)


class Business(Base):

    __tablename__ = "business"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)


class Symptom(Base):

    __tablename__ = "symptom"

    code = Column(String(255), primary_key=True)
    diagnostic = Column(Boolean, nullable=False)

