import uuid
from urllib.parse import urlencode
from pathlib import Path
import requests
from typing import Tuple

from repositories import PrescriptionRepo, AuditRepo 

QR_OUTPUT_DIR = "qr_codes"
QR_BASE_URL = "https://api.qrserver.com/v1/create-qr-code/"


def _ensure_output_dir() -> Path:
    p = Path(QR_OUTPUT_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_pickup_code() -> str:
    return uuid.uuid4().hex[:10].upper()

def ensure_pickup_code_and_qr(prescription_id: int) -> Tuple[str, str]:
    """
    Ensure the prescription has a pickup_code and QR image.
    Returns (pickup_code, qr_path).
    """
    existing = PrescriptionRepo.get_pickup_code_by_id(prescription_id)
    if existing is not None:
        code, path = existing
        if code and path:
            return code, path

    # otherwise generate new QR
    pickup_code = generate_pickup_code()
    params = {"size": "200x200", "data": pickup_code}
    url = f"{QR_BASE_URL}?{urlencode(params)}"

    out_dir = _ensure_output_dir()
    filename = f"prescription_{prescription_id}_{pickup_code}.png"
    out_path = out_dir / filename

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(resp.content)

    PrescriptionRepo.update_pickup_qr(
        prescription_id=prescription_id,
        pickup_code=pickup_code,
        qr_path=str(out_path),
    )

    AuditRepo.record_event(
        "QR_GENERATED",
        f"prescription_id={prescription_id};pickup_code={pickup_code};path={out_path}",
    )

    return pickup_code, str(out_path)


def generate_qr_for_prescription(prescription_id: int) -> str:
        pickup_code, path = ensure_pickup_code_and_qr(prescription_id)
        return path
