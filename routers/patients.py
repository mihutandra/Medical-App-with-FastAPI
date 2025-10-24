from typing import Optional
from fastapi import APIRouter, HTTPException, status
from sqlmodel import SQLModel, Session, select

from db.session import engine
from models.models import Patient

router = APIRouter(prefix="/patients", tags=["Patients"])

class PatientUpdate(SQLModel):
    id: Optional[int] = None
    name: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None 
    email: Optional[str] = None

@router.post("/", response_model=Patient)
def create_patient(patient: Patient):
    with Session(engine) as session:
        session.add(patient)
        session.commit()
        session.refresh(patient)
        return patient

@router.get("/", response_model=list[Patient])
def get_patients():
    with Session(engine) as session:
        patients = session.exec(select(Patient)).all()
        return patients

@router.get("/{patient_id}", response_model=Patient)
def get_patient_by_id(patient_id: int):
    with Session(engine) as session:
        patient = session.get(Patient, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient

@router.patch("/{patient_id}", response_model=Patient)
def update_patient(patient_id: int, payload: PatientUpdate):
    """
    Partial update (PATCH). Only updates fields provided in the payload.
    """
    with Session(engine) as session:
        patient = session.get(Patient, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if payload.name is not None:
            patient.name = payload.name
        if payload.age is not None:
            patient.age = payload.age
        if payload.phone is not None:
            patient.phone = payload.phone
        if payload.email is not None:
            patient.email = payload.email

        session.add(patient)
        session.commit()
        session.refresh(patient)
        return patient
        
@router.put("/{patient}", response_model=Patient, status_code=status.HTTP_200_OK)
def replace_patient(patient_id: int, replacement: Patient) -> Patient:
    """
    Full update (PUT). Replaces all updatable fields of the existing patient
    with the values from `replacement`. The `id` in path wins.
    """
    with Session(engine) as session:
        pat = session.get(Patient, patient_id)
        if not pat:
            raise HTTPException(status_code=404, detail="Patient not found")

        # overwrite fields
        pat.name = replacement.name
        pat.age = replacement.age
        pat.phone = replacement.phone
        pat.email = replacement.email

        session.add(pat)
        session.commit()
        session.refresh(pat)
        return pat

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_patient(patient_id: int) -> None:
    """Soft delete: mark is_active=False, keep history."""
    with Session(engine) as session:
        pat = session.get(Patient, patient_id)
        if not pat:
            raise HTTPException(status_code=404, detail="Patient not found")
        if not pat.is_active:
            return None 
        pat.is_active = False
        session.add(pat)
        session.commit()
        return None


@router.post("/{patient_id}/restore", response_model=Patient)
def restore_patient(patient_id: int):
    """Restore a soft-deleted patient (is_active=True)."""
    with Session(engine) as session:
        pat = session.get(Patient, patient_id)
        if not pat:
            raise HTTPException(status_code=404, detail="Patient not found")
        if pat.is_active:
            return pat  
        pat.is_active = True
        session.add(pat)
        session.commit()
        session.refresh(pat)
        return pat