"""
Repository Pattern:
All SQL access is centralized here. Higher layers work with Patient and Prescription
domain objects instead of raw database rows or psycopg2 cursors.
"""

from typing import Optional, List,Tuple
from db import db_cursor
from models import Patient, Prescription
from datetime import datetime

# Health card numbers are stored hex-encoded in the database for privacy.
# These helpers convert between plain text and hex at the repository boundary.
def _hcn_to_hex(hcn: str) -> str:
    """Convert a health card number to a hex string for storage."""
    return hcn.encode("utf-8").hex()

def _hcn_from_hex(h: str) -> str:
    """Convert stored hex back to the original health card number."""
    return bytes.fromhex(h).decode("utf-8")

class PatientRepo:
    @staticmethod
    def create(p: Patient) -> Patient:
        sql = """
        INSERT INTO patients (health_card_no, first_name, last_name, date_of_birth, phone, email)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, created_at;
        """
        with db_cursor() as cur:
            cur.execute(sql, (_hcn_to_hex(p.health_card_no), p.first_name, p.last_name,
                              p.date_of_birth, p.phone, p.email))
            row = cur.fetchone()
        p.id = row["id"]
        p.created_at = row["created_at"]
        return p

    @staticmethod
    def get_by_health_card(hcn: str) -> Optional[Patient]:
        sql = """
        SELECT id, health_card_no, first_name, last_name, date_of_birth, phone, email, created_at
        FROM patients
        WHERE health_card_no = %s;
        """
        with db_cursor() as cur:
            cur.execute(sql, (_hcn_to_hex(hcn),))
            row = cur.fetchone()
        if not row:
            return None
        return Patient(
            id=row["id"],
            health_card_no=_hcn_from_hex(row["health_card_no"]),
            first_name=row["first_name"],
            last_name=row["last_name"],
            date_of_birth=row["date_of_birth"],
            phone=row["phone"],
            email=row["email"],
            created_at=row["created_at"],
        )
    
    @staticmethod
    def get_by_id(patient_id: int) -> Optional[Patient]:
        sql = """
        SELECT id, health_card_no, first_name, last_name,
               date_of_birth, phone, email, created_at
        FROM patients
        WHERE id = %s;
        """
        with db_cursor() as cur:
            cur.execute(sql, (patient_id,))
            row = cur.fetchone()
        if not row:
            return None
        return Patient(
            id=row["id"],
            health_card_no=_hcn_from_hex(row["health_card_no"]),
            first_name=row["first_name"],
            last_name=row["last_name"],
            date_of_birth=row["date_of_birth"],
            phone=row["phone"],
            email=row["email"],
            created_at=row["created_at"],
        )
    
    # Allows the pharmacist to fill in missing phone/email during notification.
    # Changes are persisted so future notifications do not need to prompt again.
    @staticmethod
    def update_contact(
        patient_id: int,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        updates = []
        params = []
        if phone is not None:
            updates.append("phone = %s")
            params.append(phone)
        if email is not None:
            updates.append("email = %s")
            params.append(email)
        if not updates:
            return
        sql = f"""
        UPDATE patients
        SET {", ".join(updates)}
        WHERE id = %s;
        """
        params.append(patient_id)
        with db_cursor() as cur:
            cur.execute(sql, tuple(params))


class PrescriptionRepo:
    @staticmethod
    def get_pickup_code_by_id(
        prescription_id: int,
    ) -> Optional[Tuple[Optional[str], Optional[str]]]:
        sql = """
        SELECT pickup_code, pickup_qr_path
        FROM prescriptions
        WHERE id = %s;
        """
        with db_cursor() as cur:
            cur.execute(sql, (prescription_id,))
            row = cur.fetchone()
        if not row:
            return None
        return row["pickup_code"], row["pickup_qr_path"]
    
    @staticmethod
    def create(p: Prescription) -> Prescription:
        sql = """
        INSERT INTO prescriptions (patient_id, drug_name, dosage, instructions, status, pickup_code, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at;
        """
        with db_cursor() as cur:
            cur.execute(sql, (p.patient_id, p.drug_name, p.dosage,
                              p.instructions, p.status, p.pickup_code, p.expires_at))
            row = cur.fetchone()
        p.id = row["id"]
        p.created_at = row["created_at"]
        return p

    @staticmethod
    def update_pickup_qr(prescription_id: int, pickup_code: str, qr_path: str) -> None:
        sql = """
        UPDATE prescriptions
        SET pickup_code = %s,
            pickup_qr_path = %s
        WHERE id = %s;
        """
        with db_cursor() as cur:
            cur.execute(sql, (pickup_code, qr_path, prescription_id))

    @staticmethod
    def list_for_patient(patient_id: int) -> List[Prescription]:
        sql = """
        SELECT id, patient_id, drug_name, dosage, instructions, status,
               pickup_code, pickup_qr_path, expires_at, created_at, picked_up_at
        FROM prescriptions
        WHERE patient_id = %s
        ORDER BY created_at DESC;
        """
        with db_cursor() as cur:
            cur.execute(sql, (patient_id,))
            rows = cur.fetchall()
        result = []
        for r in rows:
            result.append(
                Prescription(
                    id=r["id"],
                    patient_id=r["patient_id"],
                    drug_name=r["drug_name"],
                    dosage=r["dosage"],
                    instructions=r["instructions"],
                    status=r["status"],
                    pickup_code=r["pickup_code"],
                    pickup_qr_path=r["pickup_qr_path"],
                    expires_at=r["expires_at"],
                    created_at=r["created_at"],
                    picked_up_at=r["picked_up_at"],
                )
            )
        return result
    
    @staticmethod
    def get_by_pickup_code(code: str) -> Optional[Prescription]:
        sql = """
        SELECT id, patient_id, drug_name, dosage, instructions, status,
               pickup_code, pickup_qr_path, expires_at, created_at, picked_up_at
        FROM prescriptions
        WHERE pickup_code = %s;
        """
        with db_cursor() as cur:
            cur.execute(sql, (code,))
            row = cur.fetchone()
        if not row:
            return None
        return Prescription(
            id=row["id"],
            patient_id=row["patient_id"],
            drug_name=row["drug_name"],
            dosage=row["dosage"],
            instructions=row["instructions"],
            status=row["status"],
            pickup_code=row["pickup_code"],
            pickup_qr_path=row["pickup_qr_path"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
            picked_up_at=row["picked_up_at"],
        )

    @staticmethod
    def mark_dispensed(prescription_id: int) -> None:
        sql = """
        UPDATE prescriptions
        SET status = 'DISPENSED',
            picked_up_at = NOW()
        WHERE id = %s;
        """
        with db_cursor() as cur:
            cur.execute(sql, (prescription_id,))
    
    @staticmethod
    def list_dispensed() -> List[Prescription]:
        """
        Return all dispensed prescriptions, most recent first.
        """
        sql = """
        SELECT id, patient_id, drug_name, dosage, instructions, status,
               pickup_code, pickup_qr_path, expires_at, created_at, picked_up_at
        FROM prescriptions
        WHERE status = 'DISPENSED'
        ORDER BY picked_up_at DESC NULLS LAST, created_at DESC;
        """
        with db_cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        result: List[Prescription] = []
        for r in rows:
            result.append(
                Prescription(
                    id=r["id"],
                    patient_id=r["patient_id"],
                    drug_name=r["drug_name"],
                    dosage=r["dosage"],
                    instructions=r["instructions"],
                    status=r["status"],
                    pickup_code=r["pickup_code"],
                    pickup_qr_path=r["pickup_qr_path"],
                    expires_at=r["expires_at"],
                    created_at=r["created_at"],
                    picked_up_at=r["picked_up_at"],
                )
            )
        return result
    
    @staticmethod
    def get_by_id(prescription_id: int) -> Optional[Prescription]:
        sql = """
        SELECT id, patient_id, drug_name, dosage, instructions, status,
               pickup_code, pickup_qr_path, expires_at, created_at, picked_up_at
        FROM prescriptions
        WHERE id = %s;
        """
        with db_cursor() as cur:
            cur.execute(sql, (prescription_id,))
            row = cur.fetchone()
        if not row:
            return None
        return Prescription(
            id=row["id"],
            patient_id=row["patient_id"],
            drug_name=row["drug_name"],
            dosage=row["dosage"],
            instructions=row["instructions"],
            status=row["status"],
            pickup_code=row["pickup_code"],
            pickup_qr_path=row["pickup_qr_path"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
            picked_up_at=row["picked_up_at"],
        )
    
# Single entry point for writing to audit_log. All important actions (patient created,
# prescription created, notify, dispense, report export) call this for traceability.
class AuditRepo:
    @staticmethod
    def record_event(event_type: str, payload: str) -> None:
        sql = """
        INSERT INTO audit_log (event_type, payload)
        VALUES (%s, %s);
        """
        with db_cursor() as cur:
            cur.execute(sql, (event_type, payload))

