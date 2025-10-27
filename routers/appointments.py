from datetime import time
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status
from pydantic import field_validator, BaseModel
from sqlmodel import SQLModel, Field, Session, select

from db.session import engine
from models.models import Doctor, DoctorSchedule
router = APIRouter(prefix="/appointments", tags=["Appointments"])

