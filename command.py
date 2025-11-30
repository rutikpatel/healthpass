# command.py
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from typing import Optional, List

from services.patient_service import register_patient
from services.prescription_service import (
    create_prescription_for_patient,
    list_prescriptions,
)
from services.qr_service import generate_qr_for_prescription
from repositories import PatientRepo, PrescriptionRepo, AuditRepo
from models import Prescription
from notifier import NotifierFactory


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        ...


class AddPatientCommand(Command):
    def __init__(
        self,
        health_card_no: str,
        first_name: str,
        last_name: str,
        dob: date,
        phone: Optional[str],
        email: Optional[str],
    ) -> None:
        self.health_card_no = health_card_no
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.phone = phone
        self.email = email

    def execute(self) -> None:
        patient = register_patient(
            health_card_no=self.health_card_no,
            first_name=self.first_name,
            last_name=self.last_name,
            dob=self.dob,
            phone=self.phone,
            email=self.email,
        )
        # AUDIT: patient created
        AuditRepo.record_event(
            "PATIENT_CREATED",
            f"patient_id={patient.id};hcn={patient.health_card_no}",
        )


class NewPrescriptionCommand(Command):
    def __init__(
        self,
        health_card_no: str,
        drug_name: str,
        dosage: str,
        instructions: Optional[str],
        days_valid: int,
    ) -> None:
        self.health_card_no = health_card_no
        self.drug_name = drug_name
        self.dosage = dosage
        self.instructions = instructions
        self.days_valid = days_valid

    def execute(self) -> None:
        patient = PatientRepo.get_by_health_card(self.health_card_no)
        if not patient:
            raise ValueError("No patient found with that health card number.")
        prescription = create_prescription_for_patient(
            patient_id=patient.id,
            drug_name=self.drug_name,
            dosage=self.dosage,
            instructions=self.instructions,
            days_valid=self.days_valid,
        )
        # AUDIT: prescription created
        AuditRepo.record_event(
            "RX_CREATED",
            f"prescription_id={prescription.id};patient_id={patient.id}",
        )


class GeneratePickupQRCommand(Command):
    def __init__(self, prescription_id: int) -> None:
        self.prescription_id = prescription_id

    def execute(self) -> None:
        path = generate_qr_for_prescription(self.prescription_id)
        # qr_service already audits QR_GENERATED
        print(f"QR image generated at {path}")

class DispensePrescriptionCommand(Command):
    def __init__(self, pickup_code: str) -> None:
        self.pickup_code = pickup_code

    def execute(self) -> None:
        p = PrescriptionRepo.get_by_pickup_code(self.pickup_code)
        if not p:
            raise ValueError("No prescription found for that pickup code.")

        if p.status == "DISPENSED":
            raise ValueError("Prescription already dispensed.")

        if p.expires_at is not None:
            now_utc = datetime.now(timezone.utc)
            if p.expires_at < now_utc:
                raise ValueError("Prescription has expired and cannot be dispensed.")

        PrescriptionRepo.mark_dispensed(p.id)

        # AUDIT: prescription dispensed
        AuditRepo.record_event(
            "RX_DISPENSED",
            f"prescription_id={p.id};pickup_code={self.pickup_code}",
        )

class ReportDispensedCommand(Command):
    """
    Generate a report of all dispensed prescriptions.

    The Command sets self.rows to a list of Prescription domain objects.
    The CLI layer is responsible for formatting/printing the report.
    """
    def __init__(self) -> None:
        self.rows: List[Prescription] = []

    def execute(self) -> None:
        self.rows = PrescriptionRepo.list_dispensed()
        # optional audit: that a report was generated
        AuditRepo.record_event(
            "REPORT_DISPENSED_GENERATED",
            f"count={len(self.rows)}",
        )

