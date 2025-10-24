from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, select

from db.session import engine
from models.models import Doctor, Appointment, AppointmentStatus
from sqlmodel import SQLModel, Field

router = APIRouter(prefix="/doctors", tags=["Doctors"])


class DoctorUpdate(SQLModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    price_per_consultation: Optional[Decimal] = None


@router.post("/", response_model=Doctor)
def create_doctor(doctor: Doctor):
    with Session(engine) as session:
        session.add(doctor)
        session.commit()
        session.refresh(doctor)
        return doctor

@router.get("/", response_model=list[Doctor])
def get_doctors():
    with Session(engine) as session:
        doctors = session.exec(select(Doctor)).all()
        return doctors
    
@router.get("/{doctor_id}")
def get_doctors_by_id(doctor_id: int):
    with Session(engine) as session:
        doctors = session.exec(
            select(Doctor).where(Doctor.id == doctor_id)
        ).all()
        return doctors


@router.get("/{doctor_specialty}")
def get_doctors_by_specialty(doctor_specialty: str):
    with Session(engine) as session:
        doctors = session.exec(
            select(Doctor).where(Doctor.specialty == doctor_specialty)
        ).all()
        return doctors


@router.patch("/{doctor_id}", response_model=Doctor, status_code=status.HTTP_200_OK)
def update_doctor(doctor_id: int, payload: DoctorUpdate):
    """
    Partial update (PATCH). Only updates fields provided in the payload.
    """
    with Session(engine) as session:
        doc = session.get(Doctor, doctor_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Doctor not found")

        if payload.name is not None:
            doc.name = payload.name
        if payload.specialty is not None:
            doc.specialty = payload.specialty
        if payload.phone is not None:
            doc.phone = payload.phone
        if payload.email is not None:
            doc.email = payload.email
        if payload.price_per_consultation is not None:
            doc.price_per_consultation = payload.price_per_consultation

        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc

@router.put("/{doctor_id}", response_model=Doctor, status_code=status.HTTP_200_OK)
def replace_doctor(doctor_id: int, replacement: Doctor) -> Doctor:
    """
    Full update (PUT). Replaces all updatable fields of the existing doctor
    with the values from `replacement`. The `id` in path wins.
    """
    with Session(engine) as session:
        doc = session.get(Doctor, doctor_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Doctor not found")

        # overwrite fields
        doc.name = replacement.name
        doc.specialty = replacement.specialty
        doc.phone = replacement.phone
        doc.email = replacement.email
        doc.price_per_consultation = replacement.price_per_consultation

        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc

@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(doctor_id: int) -> None:
    """
    Delete a doctor. By default we block deletion if the doctor has FUTURE scheduled appointments.
    Change behavior if you prefer hard delete regardless.
    """
    with Session(engine) as session:
        doc = session.get(Doctor, doctor_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Doctor not found")

        # Check for future appointments
        future_appointments=session.exec(
            select(Appointment).where(
                (Appointment.doctor_id == doctor_id) &
                (Appointment.appointment_datetime > datetime.now(timezone.utc)) &
                (Appointment.status == AppointmentStatus.scheduled)
            )
        )
        if future_appointments.first():
            raise HTTPException(
                status_code=400,
                detail="Cannot delete doctor with future scheduled appointments."
            )
        session.delete(doc)
        session.commit()    
    return None
