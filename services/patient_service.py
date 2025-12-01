from datetime import date
from typing import Optional
from models import Patient
from repositories import PatientRepo

#  register a new patient using their health card number and personal details
def register_patient(
    health_card_no: str,
    first_name: str,
    last_name: str,
    dob: date,
    phone: Optional[str],
    email: Optional[str],
) -> Patient:
    existing = PatientRepo.get_by_health_card(health_card_no)
    if existing is not None:
        raise ValueError("Patient with this health card already exists")
    patient = Patient(
        id=None,
        health_card_no=health_card_no,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        phone=phone,
        email=email,
    )
    return PatientRepo.create(patient)
