import pytest
from fastapi.testclient import TestClient
from main import medical_app
from db.session import engine
from sqlmodel import Session
from models.models import Patient

@pytest.fixture()
def client():
    """FastAPI test client."""
    return TestClient(medical_app)

def delete_patient_after_test(patient_id: int):
    with Session(engine) as session:
       patient = session.get(Patient, patient_id)
       if patient:
           session.delete(patient)
           session.commit()
           
# Test Create Patients Endpoint
def test_create_patients(client):
    data = {
        "id": "1234567890123",
        "name": "Test Patient",
        "age": 30,
        "phone": "0700000000",
        "email": "test@example.com"
    }
    response = client.post("/patients/", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Test Patient"
    assert body["id"] == "1234567890123"
    assert body["age"] == 30
    assert body["email"] == "test@example.com"
    assert body["phone"] == "0700000000"
    assert body["is_active"] == True
    
    delete_patient_after_test(body["id"])
    
# Test Get Patients Endpoint
def test_get_patients(client):
    client.post("/patients/", json={
        "id": "9876543210987",
        "name": "Another Patient",
        "age": 25,
        "phone": "0711111111",
        "email": "another@example.com"
    })
    response = client.get("/patients/")
    assert response.status_code == 200
    patients = response.json()
    assert isinstance(patients, list)
    assert len(patients) > 0
    
    patient_id = patients[-1]["id"]
    delete_patient_after_test(patient_id)

# Test Get Patient by ID Endpoint
def test_get_patient_by_id(client):
    client.post("/patients/", json={
        "id": "9876543210987",
        "name": "Another Patient",
        "age": 25,
        "phone": "0711111111",
        "email": "another@example.com"
    })
    response = client.get("/patients/9876543210987")
    assert response.status_code == 200
    patients = response.json()
    assert isinstance(patients, dict)
    assert len(patients) == 6
    assert patients["id"] == "9876543210987"
    assert patients["name"] == "Another Patient"
    assert patients["age"] == 25
    assert patients["phone"] == "0711111111"
    assert patients["email"] == "another@example.com"
    assert patients["is_active"] == True
    
    delete_patient_after_test(9876543210987)

# Test Partial Update Patient Endpoint
def test_partial_update_patient(client):
    client.post("/patients/", json={
        "id": "9876543210987",
        "name": "Another Patient",
        "age": 25,
        "phone": "0711111111",
        "email": "another@example.com"
    })
    update_data = {
        "name": "Updated Patient",
        "age": 30,
        "phone": "0722222222",
    }
    response = client.patch("/patients/9876543210987", json=update_data)
    assert response.status_code == 202
    updated_patient = response.json()
    assert updated_patient["id"] == "9876543210987"
    assert updated_patient["name"] == "Updated Patient"
    assert updated_patient["age"] == 30
    assert updated_patient["phone"] == "0722222222"
    assert updated_patient["email"] == "another@example.com"
    assert updated_patient["is_active"] == True  
    
    delete_patient_after_test(9876543210987)  

# Test Full Update Patient Endpoint
def test_full_update_patient(client):
    response = client.post("/patients/", json={
        "id": "9876543210987",
        "name": "Another Patient",
        "age": 25,
        "phone": "0711111111",
        "email": "another@example.com"
    })
    patient = response.json()
    patient_id = patient["id"]
    update_data = {
        "name": "Updated Patient",
        "age": 30,
        "phone": "0722222222",
        "email": "updates@example.com",
    }
    print(patient_id)
    response = client.put(f"/patients/{patient_id}", json=update_data)
    assert response.status_code == 202
    updated_patient = response.json()
    assert updated_patient["id"] == "9876543210987"
    assert updated_patient["name"] == "Updated Patient"
    assert updated_patient["age"] == 30
    assert updated_patient["phone"] == "0722222222"
    assert updated_patient["email"] == "updates@example.com"
    assert updated_patient["is_active"] == True  
    
    delete_patient_after_test(9876543210987)  
    
# Test Soft Delete Patient Endpoint
def test_soft_delete_patient(client):
    response = client.post("/patients/", json={
        "id": "9876543210987",
        "name": "Another Patient",
        "age": 25,
        "phone": "0711111111",
        "email": "another@example.com"
    })
    patient_id = response.json()["id"]
    response = client.delete(f"/patients/{patient_id}")
    assert response.status_code == 204
    
    # Verify patient is marked inactive
    response = client.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    patient = response.json()
    assert patient["is_active"] == False
    
    delete_patient_after_test(9876543210987)

# Test Restore Patient Endpoint
def test_restore_patient(client):
    response = client.post("/patients/", json={
        "id": "9876543210987",
        "name": "Another Patient",
        "age": 25,
        "phone": "0711111111",
        "email": "another@example.com"
    })
    patient_id = response.json()["id"]
    response = client.delete(f"/patients/{patient_id}")
    assert response.status_code == 204
    
    # Verify patient is marked inactive
    response = client.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    patient = response.json()
    assert patient["is_active"] == False
    
    # Restore patient
    response = client.post(f"/patients/{patient_id}/restore")
    assert response.status_code == 200
    restored_patient = response.json()
    assert restored_patient["is_active"] == True
    
    delete_patient_after_test(9876543210987)