import pytest
from fastapi.testclient import TestClient
from main import medical_app
from db import session as db_session
from db.session import engine, create_db_and_tables 
from sqlmodel import Session, select
from models.models import Doctor, DoctorSchedule


@pytest.fixture(scope="function")
def client():
    # Point the app's global engine to the test one
    db_session.engine = engine
    create_db_and_tables()
    return TestClient(medical_app)

def delelete_doctor_schedule_after_test(schedule_id: int):
    with Session(engine) as session:
       schedule = session.get(DoctorSchedule, schedule_id)
       doctor = session.get(Doctor, schedule.doctor_id)
       if schedule and doctor:
           session.delete(schedule)
           session.delete(doctor)
           session.commit()

# Test Create and Get Doctor Schedules Endpoint
def test_create_doctor_schedule(client):
    # create a doctor to associate with the schedule
    doctor_response = client.post("/doctors/", json={
        "name": "Dr. ScheduleTest",
        "specialty": "Neurology",
        "phone": "0722222222",
        "email": "drSchedule@example.com",
        "price_per_consultation": 180.0
    })
    schedule_data = {
        "doctor_id": doctor_response.json()["id"],
        "weekday": 0, # Monday
        "start_time": "09:00:00",
        "end_time": "17:00:00"
    }
    doctor_id = doctor_response.json()["id"]
    response = client.post(f"/schedules/doctors/{doctor_id}", json=schedule_data)
    assert response.status_code == 201
    schedule_body = response.json()
    assert schedule_body["doctor_id"] == schedule_data["doctor_id"]
    assert schedule_body["weekday"] == schedule_data["weekday"]
    assert schedule_body["start_time"] == schedule_data["start_time"]
    assert schedule_body["end_time"] == schedule_data["end_time"]
    doctor_body = doctor_response.json()
    assert schedule_body["doctor_id"] == doctor_body["id"]
    
    
    # delete schedule after test
    schedule_id = schedule_body["id"]
    delelete_doctor_schedule_after_test(schedule_id)
    
# Test Update Doctor Schedule Endpoint
def test_update_doctor_schedule(client):
    doctor_response = client.post("/doctors/", json={
        "name": "Dr. ScheduleTest",
        "specialty": "Neurology",
        "phone": "0722222222",
        "email": "drSchedule@example.com",
        "price_per_consultation": 180.0
    })
    schedule_data = {
        "doctor_id": doctor_response.json()["id"],
        "weekday": 0, # Monday
        "start_time": "09:00:00",
        "end_time": "17:00:00"
    }
    doctor_id = doctor_response.json()["id"]
    response = client.post(f"/schedules/doctors/{doctor_id}", json=schedule_data)
    assert response.status_code == 201
    data_to_update = {
        "start_time": "10:00:00",
    }
    update_response = client.patch(f"/schedules/doctors/{doctor_id}", json=data_to_update)
    assert update_response.status_code == 202
    body_update = update_response.json()
    assert body_update["doctor_id"] == schedule_data["doctor_id"]
    assert body_update["weekday"] == schedule_data["weekday"]
    assert body_update["end_time"] == schedule_data["end_time"]
    doctor_body = doctor_response.json()
    assert body_update["doctor_id"] == doctor_body["id"]
    
    schedule_id = body_update["id"]
    delelete_doctor_schedule_after_test(schedule_id)
    
# Test Delete Doctor Schedule Endpoint
def test_delete_doctor_schedule(client):
    doctor_response = client.post("/doctors/", json={
        "name": "Dr. ScheduleTest",
        "specialty": "Neurology",
        "phone": "0722222222",
        "email": "drSchedule@example.com",
        "price_per_consultation": 180.0
    })
    schedule_data = {
        "doctor_id": doctor_response.json()["id"],
        "weekday": 0, # Monday
        "start_time": "09:00:00",
        "end_time": "17:00:00"
    }
    doctor_id = doctor_response.json()["id"]
    response = client.post(f"/schedules/doctors/{doctor_id}", json=schedule_data)
    assert response.status_code == 201
    delete_response = client.delete(f"/schedules/doctors/{doctor_id}")
    assert delete_response.status_code == 204
    with Session(engine) as session:
       doctor = session.get(Doctor,doctor_id)
       if  doctor:
           session.delete(doctor)
           session.commit()

    