# main.py
from fastapi import FastAPI
from sqlmodel import Session, select

from db.session import engine, create_db_and_tables
from models.models import Doctor
from routers import doctors, patients, schedules, appointments

medical_app = FastAPI()
medical_app.title = "Medical Appointment Scheduling API"


medical_app.include_router(doctors.router)
medical_app.include_router(patients.router)
medical_app.include_router(schedules.router)
medical_app.include_router(appointments.router)