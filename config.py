import os
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    dsn: str | None
    host: str
    port: int
    name: str
    user: str
    password: str

@dataclass
class QRServiceConfig:
    base_url: str
    output_dir: str

@dataclass
class AppConfig:
    db: DatabaseConfig
    qr: QRServiceConfig

def load_config() -> AppConfig:
    return AppConfig(
        db=DatabaseConfig(
            dsn=os.getenv("HP_DB_DSN"),  # NEW
            host=os.getenv("HP_DB_HOST", "localhost"),
            port=int(os.getenv("HP_DB_PORT", "5432")),
            name=os.getenv("HP_DB_NAME", "healthpass"),
            user=os.getenv("HP_DB_USER", "healthpass"),
            password=os.getenv("HP_DB_PASSWORD", "healthpass"),
        ),
        qr=QRServiceConfig(
            # Simple free QR API – good enough for demo
            base_url=os.getenv(
                "HP_QR_BASE_URL",
                "https://api.qrserver.com/v1/create-qr-code/"
            ),
            output_dir=os.getenv("HP_QR_OUTPUT_DIR", "qr_codes"),
        ),
    )
