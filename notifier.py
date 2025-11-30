# notifier.py
from abc import ABC, abstractmethod
from typing import Optional
import os

from models import Patient
from repositories import AuditRepo


class Notifier(ABC):
    @abstractmethod
    def notify_prescription_ready(
        self,
        patient: Patient,
        pickup_code: str,
        qr_path: Optional[str],
    ) -> None:
        """
        Notify that a prescription is ready for pickup.
        qr_path may be None if pharmacist chose not to include QR.
        """
        raise NotImplementedError


class EmailNotifier(Notifier):
    def notify_prescription_ready(
        self,
        patient: Patient,
        pickup_code: str,
        qr_path: Optional[str],
    ) -> None:
        if not patient.email:
            AuditRepo.record_event(
                "NOTIFY_EMAIL_SKIPPED",
                f"patient_id={patient.id};reason=no_email",
            )
            print("EmailNotifier: no email for patient; skipping.")
            return

        if qr_path:
            print(
                f"EmailNotifier: would send email to {patient.email} "
                f"with pickup code {pickup_code} and QR at {qr_path}"
            )
        else:
            print(
                f"EmailNotifier: would send email to {patient.email} "
                f"with pickup code {pickup_code}"
            )

        AuditRepo.record_event(
            "NOTIFY_EMAIL",
            f"patient_id={patient.id};to={patient.email};pickup_code={pickup_code};qr_included={bool(qr_path)}",
        )


class SMSNotifier(Notifier):
    def notify_prescription_ready(
        self,
        patient: Patient,
        pickup_code: str,
        qr_path: Optional[str],
    ) -> None:
        if not patient.phone:
            AuditRepo.record_event(
                "NOTIFY_SMS_SKIPPED",
                f"patient_id={patient.id};reason=no_phone",
            )
            print("SMSNotifier: no phone for patient; skipping.")
            return

        # In reality you wouldn't send QR path by SMS; but for demo we show it.
        if qr_path:
            print(
                f"SMSNotifier: would send SMS to {patient.phone} "
                f"with pickup code {pickup_code} and QR at {qr_path}"
            )
        else:
            print(
                f"SMSNotifier: would send SMS to {patient.phone} "
                f"with pickup code {pickup_code}"
            )

        AuditRepo.record_event(
            "NOTIFY_SMS",
            f"patient_id={patient.id};to={patient.phone};pickup_code={pickup_code};qr_included={bool(qr_path)}",
        )


class NotifierFactory:
    """
    HP_NOTIFY_TYPE = 'email' | 'sms'
    Default to 'email' if not set.
    """

    @staticmethod
    def create() -> Notifier:
        kind = os.getenv("HP_NOTIFY_TYPE", "email").lower()
        if kind == "email":
            return EmailNotifier()
        if kind == "sms":
            return SMSNotifier()
        raise ValueError("Unknown notifier type: %s" % kind)
