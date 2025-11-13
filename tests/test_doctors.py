import unittest
from fastapi.testclient import TestClient
from main import medical_app
from db import session  as db_session
from db.tempdb import engine as test_engine, create_db_and_tables

class TestDoctors(unittest.TestCase):

    def setUp(self):
        create_db_and_tables()
        db_session.engine = test_engine
        self.client = TestClient(medical_app)

    def test_create_doctor(self):
        data = {
            "name": "Dr. Marius Radu",
            "specialty": "Ophthalmology",
            "phone": "0789112233",
            "email": "marius@example.com",
            "price_per_consultation": 450
        }
        response = self.client.post("/doctors/", json=data)
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["name"], data["name"])
        self.assertEqual(body["specialty"], data["specialty"])
        self.assertEqual(body["phone"], data["phone"])
        self.assertEqual(body["email"], data["email"])
        self.assertEqual(body["price_per_consultation"], float(data["price_per_consultation"]))

    def test_get_doctors(self):
        # Insert one doctor first
        self.client.post("/doctors/", json={
            "name": "Dr. Andrei Manea",
            "specialty": "Cardiology",
            "phone": "0788112233",
            "email": "Andrei@example.com",
            "price_per_consultation": 150.0
        })
        response = self.client.get("/doctors")
        self.assertEqual(response.status_code, 201)
        doctors = response.json()
        self.assertIsInstance(doctors, list)
        self.assertTrue(len(doctors) > 0)

if __name__ == "__main__":
    unittest.main()
