# notifier.py
from abc import ABC, abstractmethod
from typing import Optional
import os

from services.qr_service import generate_qr_for_prescription
from repositories import AuditRepo


class Notifier(ABC):
    @abstractmethod
    def notify_prescription_ready(
        self,
        prescription_id: int,
        recipient: Optional[str],
    ) -> None:
        ...


class QRNotifier(Notifier):
    def notify_prescription_ready(
        self,
        prescription_id: int,
        recipient: Optional[str],
    ) -> None:
        path = generate_qr_for_prescription(prescription_id)
        # AUDIT: QR notification
        AuditRepo.record_event(
            "NOTIFY_QR",
            f"prescription_id={prescription_id};path={path}",
        )


class EmailNotifier(Notifier):
    def notify_prescription_ready(
        self,
        prescription_id: int,
        recipient: Optional[str],
    ) -> None:
        if not recipient:
            AuditRepo.record_event(
                "NOTIFY_EMAIL_SKIPPED",
                f"prescription_id={prescription_id};reason=no_recipient",
            )
            return

        # placeholder email behavior
        print(
            "EmailNotifier: would send email to %s about prescription #%d"
            % (recipient, prescription_id)
        )
        AuditRepo.record_event(
            "NOTIFY_EMAIL",
            f"prescription_id={prescription_id};to={recipient}",
        )


class SMSNotifier(Notifier):
    def notify_prescription_ready(
        self,
        prescription_id: int,
        recipient: Optional[str],
    ) -> None:
        if not recipient:
            AuditRepo.record_event(
                "NOTIFY_SMS_SKIPPED",
                f"prescription_id={prescription_id};reason=no_recipient",
            )
            return

        # placeholder SMS behavior
        print(
            "SMSNotifier: would send SMS to %s about prescription #%d"
            % (recipient, prescription_id)
        )
        AuditRepo.record_event(
            "NOTIFY_SMS",
            f"prescription_id={prescription_id};to={recipient}",
        )


class NotifierFactory:
    @staticmethod
    def create() -> Notifier:
        kind = os.getenv("HP_NOTIFY_TYPE", "qr").lower()
        if kind == "qr":
            return QRNotifier()
        if kind == "email":
            return EmailNotifier()
        if kind == "sms":
            return SMSNotifier()
        raise ValueError("Unknown notifier type: %s" % kind)
