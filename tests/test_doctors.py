import pytest
from fastapi.testclient import TestClient
from main import medical_app
from db.session import engine
from sqlmodel import Session
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

# Test Create Doctors Endpoint
def test_create_doctor(client):
    data = {
        "id": 9999,
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
    assert body["id"] == 9999
    assert body["specialty"] == "Ophthalmology"
    assert body["email"] == "alin@example.com"
    assert body["phone"] == "0788997766"
    
    # delete doctor after test
    doctor_id = body["id"]
    delete_doctor_after_test(doctor_id)

# Test Get Doctors Endpoint
def test_get_doctors(client):
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
    
    doctor_id = doctors[-1]["id"]
    delete_doctor_after_test(doctor_id)


# Test Get Doctor by ID Endpoint
def test_get_doctor_by_id(client):
    client.post("/doctors/", json={
        "id": 9999,
        "name": "Dr. IDTest",
        "specialty": "Neurology",
        "phone": "0711111111",
        "email": "idtest@example.com",
        "price_per_consultation": 200.0
    })
    response = client.get("/doctors/9999")
    assert response.status_code == 200
    doctors = response.json()
    assert isinstance(doctors, list)
    assert len(doctors) == 1
    assert doctors[0]["name"] == "Dr. IDTest"
    
    delete_doctor_after_test(9999)
    
    
# Test Get Doctor by Specialty Endpoint
def test_get_doctor_by_specialty(client):
    client.post("/doctors/", json={
        "name": "Dr. IDTest",
        "specialty": "Neurology",
        "phone": "0711111111",
        "email": "idtest@example.com",
        "price_per_consultation": 200.0
    })
    client.post("/doctors/", json={
        "name": "Dr. Another",
        "specialty": "Neurology",
        "phone": "0722222222",
        "email": "another@example.com",
        "price_per_consultation": 220.0
    })
    response = client.get("/doctors/specialty/Neurology")
    assert response.status_code == 200
    doctors = response.json()
    assert isinstance(doctors, list)
    assert len(doctors) == 2
    assert doctors[0]["name"] == "Dr. IDTest"
    assert doctors[1]["name"] == "Dr. Another"
    assert doctors[0]["specialty"] == "Neurology"
    assert doctors[1]["specialty"] == "Neurology"
    
    # delete doctor after test
    doctors_ids = [doc["id"] for doc in doctors]
    for doc_id in doctors_ids:
        delete_doctor_after_test(doc_id)
    
    
# Test Partial Update Doctor Endpoint
def test_partial_update_doctor(client):
    response = client.post("/doctors/", json={
        "name": "Dr. IDTest",
        "specialty": "Neurology",
        "phone": "0711111111",
        "email": "idtest@example.com",
        "price_per_consultation": 200.0
    })
    doctor = response.json()
    doctor_id = doctor["id"]
    update_data = {
        "phone": "0799999999",
        "price_per_consultation": 250.0
    }
    response = client.patch(f"/doctors/{doctor_id}", json=update_data)
    assert response.status_code == 202
    updated_doctor = response.json()
    assert updated_doctor["phone"] == "0799999999"
    assert updated_doctor["name"] == "Dr. IDTest"  
    assert updated_doctor["specialty"] == "Neurology"
    assert updated_doctor["email"] == "idtest@example.com"
    
    delete_doctor_after_test(doctor_id)
    
# Test Full Update Doctor Endpoint
def test_full_update_doctor(client):
    response = client.post("/doctors/", json={
        "name": "Dr. IDTest",
        "specialty": "Neurology",
        "phone": "0711111111",
        "email": "idtest@example.com",
        "price_per_consultation": 200.0
    })
    doctor_id = response.json()["id"]
    update_data = {
        "name": "Dr. TestUpdated",
        "specialty": "Cardiology",
        "phone": "0799999999",
        "email": "testupdated@example.com",
        "price_per_consultation": 300.0
    }
    response = client.put(f"/doctors/{doctor_id}", json=update_data)
    assert response.status_code == 202
    updated_doctor = response.json()
    assert updated_doctor["phone"] == "0799999999"
    assert updated_doctor["name"] == "Dr. TestUpdated"  
    assert updated_doctor["specialty"] == "Cardiology"
    assert updated_doctor["email"] == "testupdated@example.com"
    
    delete_doctor_after_test(doctor_id)
    
# Test Delete Doctor Endpoint
def test_delete_doctor(client):
    response = client.post("/doctors/", json={
        "name": "Dr. ToDelete",
        "specialty": "Dermatology",
        "phone": "0733333333",
        "email": "todelete@example.com",
        "price_per_consultation": 180.0
    })
    doctor = response.json()
    doctor_id = doctor["id"]
    response = client.delete(f"/doctors/{doctor_id}")
    assert response.status_code == 204
    response = client.get(f"/doctors/{doctor_id}")
    doctors = response.json()
    assert isinstance(doctors, list)
    assert len(doctors) == 0
    
    