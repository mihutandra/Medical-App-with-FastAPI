from datetime import time
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status
from pydantic import field_validator
from sqlmodel import SQLModel, Field, Session, select

from db.session import engine
from models.models import Doctor, DoctorSchedule
router = APIRouter(prefix="/doctors", tags=["Schedules"])

class ScheduleCreate(SQLModel):
    weekday: int = Field(ge=0, le=6, description="0=Mon ... 6=Sun")
    start_time: time
    end_time: time

    # @field_validator("start_time", "end_time", mode="before")
    # @classmethod
    # def validate_time_format(cls, value):
    #     """
    #     Accept only HH:MM (no seconds) and convert to time object.
    #     """
    #     if isinstance(value, time):
    #         return value
    #     if isinstance(value, str):
    #         # Match pattern HH:MM (24h)
    #         if not re.fullmatch(r"^(?:[01]\d|2[0-3]):[0-5]\d$", value):
    #             raise ValueError("Time must be in HH:MM format (no seconds)")
    #         hour, minute = map(int, value.split(":"))
    #         return time(hour, minute)
    #     raise ValueError("Invalid time format. Must be 'HH:MM'.")

class ScheduleUpdate(SQLModel):
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    # @field_validator("start_time", "end_time", mode="before")
    # @classmethod
    # def validate_time_format(cls, value):
    #     if value is None:
    #         return value
    #     if isinstance(value, time):
    #         return value
    #     if isinstance(value, str):
    #         if not re.fullmatch(r"^(?:[01]\d|2[0-3]):[0-5]\d$", value):
    #             raise ValueError("Time must be in HH:MM format (no seconds)")
    #         hour, minute = map(int, value.split(":"))
    #         return time(hour, minute)
    #     raise ValueError("Invalid time format. Must be 'HH:MM'.")
    
def doctor_or_404(session:Session, doctor_id:int) -> Doctor:
    doc = session.get(doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Doctor not found')
    return doc

def schedule_or_404(session:Session, doctor_id:int) -> DoctorSchedule:
    sch = session.get(doctor_id)
    if not sch:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return sch

def validate_time(start:time, end:time) -> None:
    if start >= end:
        raise HTTPException(status_code=404, detail="Start time must be earlier than end time")

def schedule_overlap(session:Session, doctor_id:int, start:time, end:time, weekday:int, exclude_id:Optional[int]=None ) -> bool:
    query = select(DoctorSchedule).where(
        DoctorSchedule.doctor_id == doctor_id,
        DoctorSchedule.weekday == weekday,
        DoctorSchedule.start_time > end,
        DoctorSchedule.end_time < start
    )
    if exclude_id:
        query = query.where(DoctorSchedule.id != exclude_id)
    existing = session.exec(query).first()
    return existing is not None

@router.get("/{doctor_id}/schedules", response_model=List[DoctorSchedule])
def get_doctor_schedules(doctor_id:int):
    with Session(engine) as session:
        doctor = doctor_or_404(session, doctor_id)
        return doctor.schedules
    
@router.post(
    "/{doctor_id}/schedules",
    response_model=DoctorSchedule,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule(doctor_id: int, payload: ScheduleCreate):
    validate_time(payload.start_time, payload.end_time)
    with Session(engine) as session:
        doctor_or_404(session, doctor_id)

        if schedule_overlap(session, doctor_id=doctor_id, weekday=payload.weekday, start=payload.start_time, end=payload.end_time):
            raise HTTPException(status_code=409, detail="Overlaps an existing weekly slot")

        sch = DoctorSchedule(
            doctor_id=doctor_id,
            weekday=payload.weekday,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
        session.add(sch)
        session.commit()
        session.refresh(sch)
        return sch

    