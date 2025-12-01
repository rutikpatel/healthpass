from datetime import datetime, timedelta, timezone
from typing import Optional, List
from models import Prescription
from repositories import PrescriptionRepo

def create_prescription_for_patient(
    patient_id: int,
    drug_name: str,
    dosage: str,
    instructions: Optional[str],
    days_valid: int = 7,
) -> Prescription:
    expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
    
    p = Prescription(
        id=None,
        patient_id=patient_id,
        drug_name=drug_name,
        dosage=dosage,
        instructions=instructions,
        status="ACTIVE",
        expires_at=expires_at,
    )
    return PrescriptionRepo.create(p)

def list_prescriptions(patient_id: int) -> List[Prescription]:
    return PrescriptionRepo.list_for_patient(patient_id)
