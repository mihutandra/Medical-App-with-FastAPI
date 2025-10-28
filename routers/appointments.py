# routers/appointments.py (new/updated)
from datetime import datetime, date, time, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from sqlmodel import SQLModel, Field, Session, select
import re

from db.session import engine
from models.models import Appointment, AppointmentStatus, Doctor, Patient, DoctorSchedule

router = APIRouter(prefix="/appointments", tags=["Appointments"])

class AppointmentCreate(SQLModel):
    doctor_id: int
    patient_id: str
    appointment_date: date
    start_time: time
    duration_minutes: Optional[int] = Field(default=30, ge=5, le=240)
    notes: Optional[str] = None

    # HH:MM only
    @staticmethod
    def _coerce_hhmm(v):
        if isinstance(v, time):
            return time(v.hour, v.minute)
        if isinstance(v, str):
            v = v.strip()
            if not re.fullmatch(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
                raise ValueError("Time must be HH:MM (no seconds).")
            h, m = map(int, v.split(":"))
            return time(h, m)
        raise ValueError("Invalid time format; expected HH:MM.")

    @classmethod
    def model_validate(cls, obj):
        inst = super().model_validate(obj)
        inst.start_time = cls._coerce_hhmm(inst.start_time)
        return inst

class AppointmentCancel(SQLModel):
    reason: Optional[str] = None  

def _doctor_or_404(session: Session, doctor_id: int) -> Doctor:
    doc = session.get(Doctor, doctor_id)
    if not doc:
        raise HTTPException(404, "Doctor not found")
    return doc

def _patient_or_404_active(session: Session, patient_id: str) -> Patient:
    pat = session.get(Patient, patient_id)
    if not pat or not pat.is_active:
        raise HTTPException(404, "Active patient not found")
    return pat

def _end_time(start: time, minutes: int) -> time:
    dt = datetime(2000, 1, 1, start.hour, start.minute) + timedelta(minutes=minutes)
    return time(dt.hour, dt.minute)

def _fits_doctor_schedule(session: Session, doctor_id: int, appt_date: date, start: time, end: time) -> bool:
    weekday = appt_date.weekday()
    stmt = select(DoctorSchedule).where(
        DoctorSchedule.doctor_id == doctor_id,
        DoctorSchedule.weekday == weekday,
        DoctorSchedule.start_time <= start,
        DoctorSchedule.end_time >= end,
    )
    return session.exec(stmt).first() is not None

def _overlaps_same_day(session: Session, doctor_id: int, appt_date: date, start: time, end: time, exclude_id: Optional[int] = None) -> bool:
    # overlap on the same date
    stmt = select(Appointment).where(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appt_date,
        Appointment.status == AppointmentStatus.scheduled,
    )
    if exclude_id is not None:
        stmt = stmt.where(Appointment.id != exclude_id)

    for a in session.exec(stmt):
        a_end = _end_time(a.start_time, a.duration_minutes)
        if (a.start_time < end) and (a_end > start):
            return True
    return False

def _combine_utc(d: date, t: time) -> datetime:
    # Combine date and time into a UTC datetime
    return datetime(d.year, d.month, d.day, t.hour, t.minute, tzinfo=timezone.utc)

@router.post("/", response_model=Appointment, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate):
    """Create a new appointment, ensuring no conflicts and within doctor's schedule."""
    
    with Session(engine) as session:
        _doctor_or_404(session, payload.doctor_id)
        _patient_or_404_active(session, payload.patient_id)

        start = payload.start_time
        end = _end_time(start, payload.duration_minutes or 30)

        if not _fits_doctor_schedule(session, payload.doctor_id, payload.appointment_date, start, end):
            raise HTTPException(422, "Appointment is outside doctor's schedule for that day")

        if _overlaps_same_day(session, payload.doctor_id, payload.appointment_date, start, end):
            raise HTTPException(409, "Appointment overlaps an existing booking")

        appt = Appointment(
            doctor_id=payload.doctor_id,
            patient_id=payload.patient_id,
            appointment_date=payload.appointment_date,
            start_time=start,
            duration_minutes=payload.duration_minutes or 30,
            status=AppointmentStatus.scheduled,
            notes=payload.notes,
        )
        session.add(appt)
        session.commit()
        session.refresh(appt)
        return appt



@router.get("/patients/{patient_id}")
def list_patient_appointments(patient_id: str):
    """List past 90 days and future appointments for a patient."""
    
    now = datetime.now(timezone.utc)
    start_window = now - timedelta(days=90)
    with Session(engine) as session:
        _patient_or_404_active(session, patient_id)

        stmt = select(Appointment).where(Appointment.patient_id == patient_id)
        appts = session.exec(stmt).all()

        past_90, future = [], []
        for a in appts:
            starts_at = _combine_utc(a.appointment_date, a.start_time)
            if starts_at >= now:
                future.append(a)
            elif starts_at >= start_window:
                past_90.append(a)

        past_90.sort(key=lambda x: (x.appointment_date, x.start_time), reverse=True)
        future.sort(key=lambda x: (x.appointment_date, x.start_time))
        return {"past_90_days": past_90, "future": future}

@router.get("/doctors/{doctor_id}", response_model=list[Appointment])
def list_doctor_future_appointments(doctor_id: int):
    """List future appointments for a doctor."""
    
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        _doctor_or_404(session, doctor_id)
        appts = session.exec(
            select(Appointment).where(Appointment.doctor_id == doctor_id)
        ).all()
        future = [a for a in appts if _combine_utc(a.appointment_date, a.start_time) >= now]
        future.sort(key=lambda x: (x.appointment_date, x.start_time))
        return future

@router.patch("/{appointment_id}/cancel", response_model=Appointment)
def cancel_appointment(appointment_id: int):
    """Cancel a scheduled appointment by changing its status."""
    with Session(engine) as session:
        appt = session.get(Appointment, appointment_id)
        if not appt:
            raise HTTPException(404, "Appointment not found")
        if appt.status != AppointmentStatus.scheduled:
            raise HTTPException(409, "Only scheduled appointments can be cancelled")
        appt.status = AppointmentStatus.cancelled
        session.add(appt)
        session.commit()
        session.refresh(appt)
        return appt
