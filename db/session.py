from __future__ import annotations
import os
from sqlmodel import SQLModel, create_engine

sqlite_file_name = "medical_app.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)
def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)