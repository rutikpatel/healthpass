from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

# Simple domain models used throughout the application. These are returned by
# repositories and passed into commands and services.
@dataclass
class Patient:
    id: Optional[int]
    health_card_no: str
    first_name: str
    last_name: str
    date_of_birth: date
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Prescription:
    id: Optional[int]
    patient_id: int
    drug_name: str
    dosage: str
    instructions: Optional[str]
    status: str = "ACTIVE"
    pickup_code: Optional[str] = None
    pickup_qr_path: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None

@dataclass
class AuditLog:
    id: Optional[int]
    event_type: str
    payload: Optional[str] = None
    created_at: Optional[datetime] = None