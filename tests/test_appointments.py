import pytest
from fastapi.testclient import TestClient
from main import medical_app
from db import session as db_session
from db.session import engine, create_db_and_tables
from sqlmodel import Session
from models.models import Doctor, Patient, DoctorSchedule, Appointment

@pytest.fixture(scope="function")
def client():
    # Use test DB
    db_session.engine = engine
    create_db_and_tables()
    return TestClient(medical_app)

def delete_all_after_test(doctor_id: int, patient_id: str, schedule_id: int, appointment_id: int):
    with Session(engine) as session:
        appointment = session.get(Appointment, appointment_id)
        schedule = session.get(DoctorSchedule, schedule_id)
        doctor = session.get(Doctor, doctor_id)
        patient = session.get(Patient, patient_id)

        for obj in (appointment, schedule, doctor, patient):
            if obj:
                session.delete(obj)
        session.commit()

def test_create_appointment(client):
    # Create a doctor
    doctor_response = client.post("/doctors/", json={
        "id": 9999,
        "name": "Dr. Test",
        "specialty": "Cardiology",
        "phone": "0700000000",
        "email": "test@example.com",
        "price_per_consultation": 150.0
    })
    doctor_body = doctor_response.json()

    # Create a patient
    patient_response = client.post("/patients/", json={
        "id": "9876543210987",
        "name": "Another Patient",
        "age": 25,
        "phone": "0711111111",
        "email": "another@example.com"
    })
    patient_body = patient_response.json()

    # Create a schedule
    schedule_data = {
        "weekday": 0,  # Monday
        "start_time": "09:00",
        "end_time": "17:00"
    }
    schedule_response = client.post(f"/schedules/doctors/{doctor_body['id']}", json=schedule_data)
    schedule_body = schedule_response.json()

    # Create an appointment
    appointment_data = {
        "doctor_id": doctor_body["id"],
        "patient_id": patient_body["id"],
        "appointment_date": "2025-11-24",
        "start_time": "10:00:00",
        "duration_minutes": 30,
        "notes": "Regular check-up"
    }
    appointment_response = client.post("/appointments/", json=appointment_data)
    assert appointment_response.status_code == 201

    appointment_body = appointment_response.json()
    assert appointment_body["doctor_id"] == doctor_body["id"]
    assert appointment_body["patient_id"] == patient_body["id"]
    assert appointment_body["appointment_date"] == appointment_data["appointment_date"]
    assert appointment_body["start_time"] == appointment_data["start_time"]
    assert appointment_body["duration_minutes"] == appointment_data["duration_minutes"]
    assert appointment_body["notes"] == appointment_data["notes"]

    # Cleanup
    delete_all_after_test(
        doctor_body["id"],
        patient_body["id"],
        schedule_body["id"],
        appointment_body["id"]
    )

# Test Ge Past 90 Days and Future Appointments for a Patient Endpoint
def test_get_patient_appointments(client):
    # Create a doctor
    doctor_response = client.post("/doctors/", json={
        "id": 9999,
        "name": "Dr. Test",
        "specialty": "Cardiology",
        "phone": "0700000000",
        "email": "test@example.com",
        "price_per_consultation": 150.0
    })
    doctor_body = doctor_response.json()

    # Create a patient
    patient_response = client.post("/patients/", json={
        "id": "9876543210987",
        "name": "Another Patient",
        "age": 25,
        "phone": "0711111111",
        "email": "another@example.com"
    })
    patient_body = patient_response.json()

    # Create a schedule
    schedule_data = {
        "weekday": 0,  # Monday
        "start_time": "09:00",
        "end_time": "17:00"
    }
    schedule_response = client.post(f"/schedules/doctors/{doctor_body['id']}", json=schedule_data)
    schedule_body = schedule_response.json()

    # Create an appointment
    appointment_data = {
        "doctor_id": doctor_body["id"],
        "patient_id": patient_body["id"],
        "appointment_date": "2025-11-10",
        "start_time": "10:00:00",
        "duration_minutes": 30,
        "notes": "Regular check-up"
    }
    appointment_response = client.post("/appointments/", json=appointment_data)
    assert appointment_response.status_code == 201
    