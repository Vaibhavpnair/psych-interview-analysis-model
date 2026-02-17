"""
Patient API endpoints.
Handles patient records and cross-session history.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.schemas.patient import PatientCreate, PatientResponse, PatientHistory

router = APIRouter()


from app.models.patient import Patient
from app.models.session import InterviewSession
from sqlalchemy import func

@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all patients (anonymized IDs) with session counts."""
    patients = db.query(Patient).offset(skip).limit(limit).all()
    
    # Calculate session counts for each patient
    result = []
    for p in patients:
        session_count = db.query(InterviewSession).filter(InterviewSession.patient_id == p.id).count()
        # Create a dict that matches PatientResponse
        patient_dict = {
            "id": p.id,
            "anonymous_id": p.anonymous_id,
            "age_range": p.age_range,
            "gender": p.gender,
            "created_at": p.created_at,
            "total_sessions": session_count
        }
        result.append(patient_dict)
        
    return result


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Register a new patient (with anonymized ID)."""
    # Check if anonymous_id already exists
    existing = db.query(Patient).filter(Patient.anonymous_id == patient_data.anonymous_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")

    new_patient = Patient(
        anonymous_id=patient_data.anonymous_id,
        age_range=patient_data.age_range,
        gender=patient_data.gender,
        notes=patient_data.notes
    )
    
    db.add(new_patient)
    try:
        db.commit()
        db.refresh(new_patient)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    # Return with total_sessions=0
    return {
        "id": new_patient.id,
        "anonymous_id": new_patient.anonymous_id,
        "age_range": new_patient.age_range,
        "gender": new_patient.gender,
        "created_at": new_patient.created_at,
        "total_sessions": 0
    }


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get patient details by ID."""
    # TODO: Query patient from database
    raise HTTPException(status_code=404, detail="Patient not found")


@router.get("/{patient_id}/history", response_model=PatientHistory)
async def get_patient_history(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns trend data across multiple sessions.
    Enables comparison of current session vs baseline.
    """
    # TODO: Aggregate cross-session metrics
    return PatientHistory(
        patient_id=patient_id,
        total_sessions=0,
        sessions=[],
        trend_summary="No sessions recorded yet.",
    )
