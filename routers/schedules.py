from datetime import time
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status
from pydantic import field_validator, BaseModel
from sqlmodel import SQLModel, Field, Session, select

from db.session import engine
from models.models import Doctor, DoctorSchedule
router = APIRouter(prefix="/schedules", tags=["Schedules"])

class ScheduleCreate(SQLModel):
    weekday: int = Field(ge=0, le=6, description="0=Mon ... 6=Sun")
    start_time: time
    end_time: time

class ScheduleUpdate(SQLModel):
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class ScheduleOut(SQLModel):
    weekday: str
    start_time: str
    end_time: str

def doctor_or_404(session:Session, doctor_id:int) -> Doctor:
    doc = session.get(Doctor, doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Doctor not found')
    return doc

def schedule_or_404(session:Session, doctor_id:int) -> DoctorSchedule:
    sch = session.get(DoctorSchedule, doctor_id)
    if not sch:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return sch

def validate_time(start:time, end:time) -> None:
    if start >= end:
        raise HTTPException(status_code=409, detail="Start time must be earlier than end time")

def schedule_overlap(
    session: Session,
    doctor_id: int,
    start: time,
    end: time,
    weekday: int,
    exclude_id: Optional[int] = None,
) -> bool:
    """
    Returns True if ANY existing weekly slot overlaps [start, end) on the same weekday.
    Touching endpoints (end == start) are allowed (no overlap).
    """
    q = (
        select(DoctorSchedule)
        .where(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.weekday == weekday,
            DoctorSchedule.start_time < end,   # existing starts before the new ends
            DoctorSchedule.end_time > start,   # existing ends after the new starts
        )
    )
    if exclude_id is not None:
        q = q.where(DoctorSchedule.id != exclude_id)

    return session.exec(q).first() is not None

@router.get("/doctors/{doctor_id}", response_model=list[ScheduleOut], status_code=status.HTTP_200_OK)
def get_doctor_schedules(doctor_id:int):
    with Session(engine) as session:
        doctor = doctor_or_404(session, doctor_id)
        schedules = doctor.schedules
        schedules.sort(key=lambda x: x.weekday)
        result = [] 
        for s in schedules:
            result.append(ScheduleOut(
                weekday=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][s.weekday],
                start_time=s.start_time.strftime("%H:%M"),
                end_time=s.end_time.strftime("%H:%M"),
            ))
        return result
    
@router.post(
    "/doctors/{doctor_id}",
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

@router.patch(
    "/doctors/{doctor_id}", response_model=DoctorSchedule, status_code=status.HTTP_202_ACCEPTED)
def update_schedule(doctor_id:int, payload:ScheduleUpdate):
    """Partial update of a doctor's schedule slot."""
    with Session(engine) as session:
        doctor_or_404(session, doctor_id)
        sch = session.exec(
            select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id)
        ).first()


        new_weekday    = payload.weekday    if payload.weekday is not None    else sch.weekday
        new_start_time = payload.start_time if payload.start_time is not None else sch.start_time
        new_end_time   = payload.end_time   if payload.end_time is not None   else sch.end_time

        validate_time(new_start_time, new_end_time)

        sch.weekday    = new_weekday
        sch.start_time = new_start_time 
        sch.end_time   = new_end_time

        session.add(sch)
        session.commit()
        session.refresh(sch)
        return sch
    
@router.delete(
    "/doctors/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(doctor_id:int) -> None:
    """Delete a doctor's schedule slot."""
    with Session(engine) as session:
        doctor_or_404(session, doctor_id)
        sch = session.exec(
            select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id)
        ).first()
        if not sch:
            raise HTTPException(status_code=404, detail="Schedule not found")
        session.delete(sch)
        session.commit()
        return None