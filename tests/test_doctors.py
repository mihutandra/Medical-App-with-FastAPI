import os
import pytest
from fastapi.testclient import TestClient
from main import medical_app
from db import session as db_session
from db.session import engine, create_db_and_tables 
from sqlmodel import Session, select
from models.models import Doctor, Appointment, AppointmentStatus

@pytest.fixture()
def client():
    """FastAPI test client."""
    return TestClient(medical_app)

def delete_doctor_after_test(doctor_id: int):
    with Session(engine) as session:
       doctor = session.get(Doctor, doctor_id)
       if doctor:
           session.delete(doctor)
           session.commit()

def test_create_doctor(client):
    data = {
        "name": "Dr. Alin",
        "specialty": "Ophthalmology",
        "phone": "0788997766",
        "email": "alin@example.com",
        "price_per_consultation": 250.0
    }
    response = client.post("/doctors/", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Dr. Alin"
    assert body["specialty"] == "Ophthalmology"
    assert body["email"] == "alin@example.com"
    
    # delete doctor after test
    doctor_id = body["id"]
    delete_doctor_after_test(doctor_id)

def test_get_doctors(client):
    # insert one
    client.post("/doctors/", json={
        "name": "Dr. Test",
        "specialty": "Cardiology",
        "phone": "0700000000",
        "email": "test@example.com",
        "price_per_consultation": 150.0
    })
    response = client.get("/doctors")
    assert response.status_code == 200
    doctors = response.json()
    assert isinstance(doctors, list)
    assert len(doctors) > 0
    
    # delete doctor after test
    doctor_id = doctors[-1]["id"]
    delete_doctor_after_test(doctor_id)
