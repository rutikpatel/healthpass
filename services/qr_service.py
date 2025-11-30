import uuid
from urllib.parse import urlencode
from pathlib import Path
import requests

from repositories import PrescriptionRepo, AuditRepo 

QR_OUTPUT_DIR = "qr_codes"
QR_BASE_URL = "https://api.qrserver.com/v1/create-qr-code/"


def _ensure_output_dir() -> Path:
    p = Path(QR_OUTPUT_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_pickup_code() -> str:
    return uuid.uuid4().hex[:10].upper()


def generate_qr_for_prescription(prescription_id: int) -> str:
    existing = PrescriptionRepo.get_pickup_code_by_id(prescription_id)
    if existing is not None:
        existing_code, existing_path = existing
        if existing_code and existing_path:
            print(f"Pickup code: {existing_code}, Path: {existing_path}")
            return existing_path 
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
    print(f"Pickup code: {pickup_code}, Path: {out_path}")

    return str(out_path)
