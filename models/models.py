from datetime import datetime, time
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import field_validator
from sqlalchemy import Column, CheckConstraint, Index, Numeric, UniqueConstraint, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql.sqltypes import DateTime, Time
from sqlmodel import Field, Relationship, SQLModel


class AppointmentStatus(str, Enum):
    scheduled = "scheduled"
    cancelled = "cancelled"
    completed = "completed"


class Doctor(SQLModel, table=True):
    __tablename__ = "doctor"
    __table_args__ = (
        UniqueConstraint("email", name="uq_doctor_email"),
        CheckConstraint("price_per_consultation >= 0", name="ck_doctor_price_nonneg"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    specialty: str
    phone: Optional[str] = None
    email: Optional[str] = None
    price_per_consultation: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False)
    )

    # Use typing.List[...] with SQLModel's Relationship
    appointments: List["Appointment"] = Relationship(back_populates="doctor")
    schedules: List["DoctorSchedule"] = Relationship(back_populates="doctor")


class Patient(SQLModel, table=True):
    __tablename__ = "patient"
    __table_args__ = (
        UniqueConstraint("email", name="uq_patient_email"),
        CheckConstraint("age >= 0", name="ck_patient_age_nonneg"),
        CheckConstraint("length(id) = 13", name="ck_patient_id_len_13"),
    )

    id: str = Field(sa_column=Column(String(13),primary_key=True , nullable=False, index=True))
    name: str = Field(index=True)
    age: int = Field(default=0, index=True)
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = Field(default=True, nullable=False)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Patient ID must contain only digits.")
        if len(v) != 13:
            raise ValueError("Patient ID must be exactly 13 digits long.")
        return v  
        
    appointments: List["Appointment"] = Relationship(back_populates="patient")
   


class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appt_doctor_dt", "doctor_id", "appointment_datetime"),
        Index("ix_appt_patient_dt", "patient_id", "appointment_datetime"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctor.id", index=True)
    patient_id: str = Field(foreign_key="patient.id", index=True)
    appointment_datetime: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    status: AppointmentStatus = Field(
        sa_column=Column(SAEnum(AppointmentStatus), nullable=False, default=AppointmentStatus.scheduled)
    )
    notes: Optional[str] = None

    doctor: "Doctor" = Relationship(back_populates="appointments")
    patient: "Patient" = Relationship(back_populates="appointments")


class DoctorSchedule(SQLModel, table=True):
    __tablename__ = "doctor_schedules"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_schedule_weekday_range"),
        CheckConstraint("start_time < end_time", name="ck_schedule_time_order"),
        Index("ix_schedule_doctor_weekday", "doctor_id", "weekday"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctor.id", index=True)
    weekday: int = Field(index=True)  # 0 Mon ... 6 Sun
    start_time: time = Field(sa_column=Column(Time, nullable=False))
    end_time: time = Field(sa_column=Column(Time, nullable=False))

    doctor: "Doctor" = Relationship(back_populates="schedules")
