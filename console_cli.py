from datetime import date
import csv
from pathlib import Path

from db import init_schema
from command import (
    AddPatientCommand,
    NewPrescriptionCommand,
    GeneratePickupQRCommand,
    DispensePrescriptionCommand,
    ReportDispensedCommand
)
from repositories import PatientRepo, AuditRepo
from services.prescription_service import list_prescriptions
from notifier import NotifierFactory

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_CSV_PATH = REPORTS_DIR / "dispensed_prescriptions.csv"


def _export_dispensed_to_csv(rows):
    """
    Overwrite the CSV with the full list of dispensed prescriptions.
    'rows' is a list[Prescription], already containing all DISPENSED rows.
    """
    with open(REPORT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "patient_id",
                "drug_name",
                "dosage",
                "status",
                "pickup_code",
                "picked_up_at",
                "created_at",
                "expires_at",
            ]
        )
        for p in rows:
            writer.writerow(
                [
                    p.id,
                    p.patient_id,
                    p.drug_name,
                    p.dosage,
                    p.status,
                    p.pickup_code or "",
                    p.picked_up_at.isoformat() if p.picked_up_at else "",
                    p.created_at.isoformat() if p.created_at else "",
                    p.expires_at.isoformat() if p.expires_at else "",
                ]
            )

    # audit export itself
    AuditRepo.record_event(
        "REPORT_DISPENSED_EXPORTED",
        f"path={REPORT_CSV_PATH};count={len(rows)}",
    )

def _read_non_empty(prompt: str) -> str:
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("Value cannot be empty.")


def _read_int(prompt: str) -> int:
    while True:
        s = input(prompt).strip()
        try:
            return int(s)
        except ValueError:
            print("Please enter a valid integer.")


def _read_date(prompt: str) -> date:
    while True:
        s = input(prompt).strip()
        try:
            y, m, d = map(int, s.split("-"))
            return date(y, m, d)
        except Exception:
            print("Use format YYYY-MM-DD (e.g., 1990-01-31).")


def action_init_db():
    print("Initializing database schema...")
    init_schema()
    print("Database schema initialized.")


def action_add_patient():
    print("\n== Add Patient ==")
    hcn = _read_non_empty("Health card number: ")
    first = _read_non_empty("First name: ")
    last = _read_non_empty("Last name: ")
    dob = _read_date("Date of birth (YYYY-MM-DD): ")
    phone = input("Phone (optional): ").strip() or None
    email = input("Email (optional): ").strip() or None

    cmd = AddPatientCommand(
        health_card_no=hcn,
        first_name=first,
        last_name=last,
        dob=dob,
        phone=phone,
        email=email,
    )
    try:
        cmd.execute()
        print("Patient created.")
    except Exception as ex:
        print("Error while creating patient:", ex)


def action_add_prescription():
    print("\n== New Prescription ==")
    hcn = _read_non_empty("Patient health card number: ")
    drug_name = _read_non_empty("Drug name: ")
    dosage = _read_non_empty("Dosage: ")
    instructions = input("Instructions (optional): ").strip() or None
    days_valid = _read_int("Days valid (default 7): ") or 7

    cmd = NewPrescriptionCommand(
        health_card_no=hcn,
        drug_name=drug_name,
        dosage=dosage,
        instructions=instructions,
        days_valid=days_valid,
    )
    try:
        cmd.execute()
        print("Prescription created.")
    except Exception as ex:
        print("Error while creating prescription:", ex)


def action_list_prescriptions():
    print("\n== List Prescriptions ==")
    hcn = _read_non_empty("Patient health card number: ")
    patient = PatientRepo.get_by_health_card(hcn)
    if not patient:
        print("No patient found with that health card number.")
        return

    presc = list_prescriptions(patient.id)
    if not presc:
        print("No prescriptions found for this patient.")
        return

    print(f"\nPrescriptions for {patient.first_name} {patient.last_name}:")
    for p in presc:
        print(
            f"- ID={p.id}, drug={p.drug_name}, dosage={p.dosage}, "
            f"status={p.status}, pickup_code={p.pickup_code or '-'}"
        )


def action_notify():
    print("\n== Notify: Prescription Ready ==")
    prescription_id = _read_int("Prescription ID: ")
    recipient = input("Recipient email/phone (optional, used for email/SMS): ").strip() or None

    notifier = NotifierFactory.create()
    try:
        notifier.notify_prescription_ready(prescription_id, recipient)
        print("Notification executed via", notifier.__class__.__name__)
    except Exception as ex:
        print("Error while notifying:", ex)


def action_generate_qr_direct():
    """
    Optional: if you want a direct 'QR only' action, bypassing the factory.
    """
    print("\n== Generate Pickup QR Directly ==")
    prescription_id = _read_int("Prescription ID: ")
    cmd = GeneratePickupQRCommand(prescription_id)
    try:
        cmd.execute()
        print("QR generated using GeneratePickupQRCommand.")
    except Exception as ex:
        print("Error while generating QR:", ex)

def action_dispense():
    print("\n== Dispense Prescription ==")
    code = _read_non_empty("Pickup code (from QR or printed text): ")
    cmd = DispensePrescriptionCommand(code)
    try:
        cmd.execute()
        print("Prescription dispensed successfully.")
    except Exception as ex:
        print("Error while dispensing prescription:", ex)

def action_report_dispensed():
    print("\n== Report: Dispensed Prescriptions ==")
    cmd = ReportDispensedCommand()
    try:
        cmd.execute()
    except Exception as ex:
        print("Error while generating report:", ex)
        return

    rows = cmd.rows
    if not rows:
        print("No dispensed prescriptions found.")
        return

    print(f"Total dispensed prescriptions: {len(rows)}")
    print("-" * 72)
    for p in rows:
        picked = p.picked_up_at or p.created_at
        print(
            f"ID={p.id} patient_id={p.patient_id} "
            f"drug={p.drug_name} dosage={p.dosage} "
            f"pickup_code={p.pickup_code or '-'} "
            f"picked_up_at={picked}"
        )

    # ask user if they want export
    choice = input("Export this report to CSV? [y/N]: ").strip().lower()
    if choice == "y":
        _export_dispensed_to_csv(rows)
        print(f"Report exported to {REPORT_CSV_PATH}")

def doctor_menu():
    while True:
        print(
            "\n=== Doctor Menu ===\n"
            "1) Add patient\n"
            "2) Add prescription\n"
            "3) List prescriptions for patient\n"
            "4) Generate pickup QR directly (Command)\n"
            "0) Back to role selection\n"
        )
        choice = input("Select option: ").strip()

        if choice == "1":
            action_add_patient()
        elif choice == "2":
            action_add_prescription()
        elif choice == "3":
            action_list_prescriptions()
        elif choice == "4":
            action_generate_qr_direct()
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please select a valid option.")


def pharmacist_menu():
    while True:
        print(
            "\n=== Pharmacist Menu ===\n"
            "1) List prescriptions for patient\n"
            "2) Dispense prescription by pickup code\n"
            "3) Notify prescription ready (Factory Method)\n"
            "4) Report dispensed prescriptions\n"
            "0) Back to role selection\n"
        )
        choice = input("Select option: ").strip()

        if choice == "1":
            action_list_prescriptions()
        elif choice == "2":
            action_dispense()
        elif choice == "3":
            action_notify()
        elif choice == "4":
            action_report_dispensed()
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please select a valid option.")

            
def main_menu():
    while True:
        print(
            "\n=== HealthPass Role Selection ===\n"
            "1) Doctor\n"
            "2) Pharmacist\n"
            "0) Exit\n"
        )
        choice = input("Select role: ").strip()

        if choice == "1":
            doctor_menu()
        elif choice == "2":
            pharmacist_menu()
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Please select a valid option.")
