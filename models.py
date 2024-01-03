import datetime
import logging
from typing import List

from sqlalchemy import String, Integer, Date, create_engine, ForeignKey, UniqueConstraint, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from flask_sqlalchemy import SQLAlchemy

class HRDBBase(DeclarativeBase):
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"

class Employee(HRDBBase):
    __tablename__ = "hrms_employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    fname: Mapped[str] =  mapped_column(String(50))
    lname: Mapped[str] =  mapped_column(String(50))
    email: Mapped[str] =  mapped_column(String(120))
    phone: Mapped[str] =  mapped_column(String(50))
    title_id: Mapped[int] = mapped_column(ForeignKey('hrms_designations.id'))
    title: Mapped["Designation"] = relationship(back_populates = "employees")

class Designation(HRDBBase):
    __tablename__ = "hrms_designations"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] =  mapped_column(String(100))
    max_leaves: Mapped[int] = mapped_column(Integer)
    employees: Mapped[List["Employee"]] = relationship(back_populates = "title")

class Leave(HRDBBase):
    __tablename__ = "hrms_leaves"
    __table_args__ = (        
        UniqueConstraint("employee_id", "date"),
        )
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date())
    employee_id: Mapped[int] = mapped_column(ForeignKey('hrms_employees.id'))
    reason: Mapped[str] =  mapped_column(String(200))


def create_all(db_uri):
    logger = logging.getLogger("HR")
    engine = create_engine(db_uri)
    HRDBBase.metadata.create_all(engine)
    logger.info("Created database")

def get_session(db_uri):
    engine = create_engine(db_uri)
    Session = sessionmaker(bind = engine)
    session = Session()
    return session