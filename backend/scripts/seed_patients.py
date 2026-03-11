import uuid
from datetime import datetime
from sqlalchemy import create_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Import models
import os
import sys

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "app"))
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.base import Base
from app.models.patient import Patient
from app.db.session import SessionLocal

def seed_patients():
    db = SessionLocal()
    try:
        # Check if we already have patients
        if db.query(Patient).count() > 0:
            print("Database already contains patients. Skipping seeding.")
            return

        dummy_patients = [
            Patient(
                anonymous_id="PAT-8821-X",
                age_range="25-30",
                gender="Male",
                notes="Baseline assessment for anxiety symptoms."
            ),
            Patient(
                anonymous_id="PAT-4432-Y",
                age_range="45-50",
                gender="Female",
                notes="Follow-up session for depressive affect."
            ),
            Patient(
                anonymous_id="PAT-0019-Z",
                age_range="18-22",
                gender="Non-binary",
                notes="Initial intake for processing speed evaluation."
            )
        ]

        db.add_all(dummy_patients)
        db.commit()
        print(f"Successfully seeded {len(dummy_patients)} patients.")
    except Exception as e:
        print(f"Error seeding patients: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_patients()
