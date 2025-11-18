# 🩺 Medical Appointment Management API

A **FastAPI-based** backend application for managing **doctors, patients, schedules, and appointments** in a medical clinic.
Built with **FastAPI**, **SQLModel**, and **SQLite/MySQL**, featuring data validation, RESTful design, and a complete automated test suite.

---

## 📘 Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Tech Stack](#tech-stack)
* [Project Structure](#project-structure)
* [Installation & Setup](#installation--setup)
* [Running the App](#running-the-app)
* [API Endpoints](#api-endpoints)
* [Data Models](#data-models)
* [Testing](#testing)
* [Contributing](#contributing)
---

## 🚀 Overview

This application provides a simple API to:

* Manage **doctors** with **their schedules** and **patients**
* Create and validate **appointments**
* Prevent overlapping schedules for doctors and bookings
* Keep patients via **soft delete** (is_active flag)
* Automatically validate Romanian CNPs (13-digit IDs)

It also includes a suite of **pytest-based tests**.

---

## ⚙️ Features

✅ **Doctors**

* CRUD operations
* Filter by specialty
* Get by ID
* Prevent deletion if future appointments exist

✅ **Patients**

* CRUD operations with soft delete
* Search by CNP (Romanian national ID)
* CNP validation (must be 13 digits)

✅ **Schedules**

* Add daily time slots for each doctor (e.g. Monday from 9:00 to 17:00)
* Prevent overlapping time slots

✅ **Appointments**

* Ensure appointments fit within doctor schedules
* Prevent double-booking
* List patient appointments (past 90 days + future)
* List doctor appointments (future only)

✅ **Tests**

* Uses **pytest**
* Full coverage of doctors, patients, schedules, and appointments

---

## 🧰 Tech Stack

| Component | Technology                           |
| --------- | ------------------------------------ |
| Framework | **FastAPI**                          |
| ORM       | **SQLModel** (SQLAlchemy + Pydantic) |
| Database  | SQLite (default), MySQL supported    |
| Testing   | **Pytest** + **FastAPI TestClient**  |
| Server    | **Uvicorn**                          |
| Language  | Python 3.10+                         |

---

## 🗂 Project Structure

```
medical_app/
│
├── main.py                         # FastAPI entrypoint
│
├── db/
│   ├── session.py                   # Production DB engine
│   └── init_db.py                   # Create DB tables
│
├── models/
│   └── models.py                    # SQLModel classes (Doctor, Schedule, Patient, Appointment, etc.)
│
├── routers/
│   ├── doctors.py                   # Endpoints for doctor CRUD
│   ├── patients.py                  # Endpoints for patient CRUD
│   ├── schedules.py                 # Endpoints for schedule management
│   └── appointments.py              # Endpoints for appointment logic
│
├── tests/
│   ├── test_doctors.py              # Unit tests for doctor routes
│   ├── test_patients.py             # Unit tests for patient routes
│   ├── test_schedules.py            # Unit tests for schedules
│   └── test_appointments.py         # Unit tests for appointments
│
├── .gitignore                       # Ignore .venv, DB files, __pycache__
├── requirements.txt                 # Dependencies
└── README.md                        # Project documentation
```

---

## 💻 Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/<your-username>/Medical-App-with-FastAPI.git
cd Medical-App-with-FastAPI
```

### 2️⃣ Create and activate a virtual environment

```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

If you don’t have the file yet, you can generate it:

```bash
pip freeze > requirements.txt
```

---

## ▶️ Running the App

### Start the FastAPI server

```bash
uvicorn main:medical_app --reload
```

Visit: Interactive Docs (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔗 API Endpoints

### 🩺 Doctors

| Method   | Endpoint        | Description                                |
| -------- | --------------- | ------------------------------------------ |
| `POST`   | `/doctors/`     | Create new doctor                          |
| `GET`    | `/doctors/`     | List all doctors (filter by `?specialty=`) |
| `GET`    | `/doctors/{doctor_id}` | Get doctor by ID                           |
| `PATCH`  | `/doctors/{doctor_id}` | Partially update doctor                    |
| `PUT`    |`/doctors/{doctor_id}` | Fully update doctor                        |
| `DELETE` | `/doctors/{doctor_id}` | Delete doctor (if no future appointments)  |
| `GET`    | `/doctors/specialty/{doctor_id}` | Get doctor by ID    

### 👩‍⚕️ Patients

| Method   | Endpoint                 | Description                          |
| -------- | ------------------------ | ------------------------------------ |
| `POST`   | `/patients/`             | Create new patient                   |
| `GET`    | `/patients/`             | List all active patients             |
| `GET`    | `/patients/{patient_id}`         | Get patient by CNP                   |
| `PATCH`  | `/patients/{patient_id}`         | Partial update                       |
| `PUT`    | `/patients/{patient_id}`         | Full update                          |
| `DELETE` | `/patients/{patient_id}`         | Soft delete (sets `is_active=False`) |
| `POST`   | `/patients/{patient_id}/restore` | Reactivate soft-deleted patient      |

### ⏰ Schedules

| Method   | Endpoint                         | Description                    |
| -------- | -------------------------------- | ------------------------------ |
| `POST`   | `/schedules/doctors/{doctor_id}` | Add schedule slot              |
| `GET`    | `/schedules/doctors/{doctor_id}` | Get all schedules for a doctor |
| `PATCH`  | `/schedules/doctors/{doctor_id}` | Update schedule slot           |
| `DELETE` | `/schedules/doctors/{doctor_id}` | Delete schedule slot           |

### 📅 Appointments

| Method  | Endpoint                      | Description                                         |
| ------- | ----------------------------- | --------------------------------------------------- |
| `POST`  | `/appointments/`              | Create appointment (checks schedule & conflicts)    |
| `GET`   | `/appointments/patients/{patient_id}` | List past 90 days + future appointments for patient |
| `GET`   | `/appointments/doctors/{doctor_id}`  | List all future appointments for doctor             |
| `PATCH` | `/appointments/{appointment_id}/cancel`   | Cancel appointment                                  |
| `PATCH` | `/appointments/{appointment_id}`          | Update appointment (validates overlap)              |

---

## 🧩 Data Models

### Doctor

| Field                  | Type  | Description               |
| ---------------------- | ----- | ------------------------- |
| id                     | int   | Primary key               |
| name                   | str   | Doctor’s name             |
| specialty              | str   | Medical specialty         |
| phone                  | str   | Contact number            |
| email                  | str   | Unique email              |
| price_per_consultation | float | Price for one appointment |

### Patient

| Field     | Type | Description                           |
| --------- | ---- | ------------------------------------- |
| id        | str  | Romanian CNP (13 digits, primary key) |
| name      | str  | Patient name                          |
| age       | int  | Age                                   |
| phone     | str  | Contact                               |
| email     | str  | Email                                 |
| is_active | bool | Soft delete flag                      |

### DoctorSchedule

| Field      | Type | Description               |
| ---------- | ---- | ------------------------- |
| id         | int  | PK                        |
| doctor_id  | int  | FK to doctor              |
| weekday    | int  | 0 = Monday ... 6 = Sunday |
| start_time | time | Schedule start            |
| end_time   | time | Schedule end              |

### Appointment

| Field            | Type | Description                           |
| ---------------- | ---- | ------------------------------------- |
| id               | int  | PK                                    |
| doctor_id        | int  | FK to doctor                          |
| patient_id       | str  | FK to patient (CNP)                   |
| appointment_date | date | Date of appointment                   |
| start_time       | time | Start time                            |
| duration_minutes | int  | Duration : 30 minutes default         |
| status           | Enum | `scheduled`, `cancelled`, `completed` |
| notes            | str  | Optional notes                        |

---

## 🧪 Testing

### Run all tests

```bash
pytest -v
```

### Run a specific test file

```bash
pytest tests/test_patients.py -v
```

### Test details

* Uses **pytest** + **FastAPI TestClient**
* Full test coverage: doctors, patients, schedules, appointments

---

