# HealthPass – Prescription Pickup Management System

HealthPass is a CLI-based prescription pickup workflow designed for small clinics and pharmacies.  
Doctors can register patients and create prescriptions; pharmacists can notify and dispense using secure pickup codes and QR codes.  
The system is backed by PostgreSQL (NeonDB), integrates with a third-party QR API, and implements all required design patterns.

---

## 1. Purpose, Audience & Overview

### Purpose
Provide a simple, auditable prescription workflow that:
- Reduces manual dispensing errors  
- Supports secure pickup using QR codes  
- Notifies patients via SMS or Email  
- Tracks all actions in an audit log  

### Audience
- Doctors  
- Pharmacy staff  
- Small clinics needing lightweight, local workflow automation  

### Core Functionalities
- Register patient (with privacy-preserving health-card hex encoding)
- Create prescriptions with expiry
- Generate QR codes via a third-party API
- Notify patients via **Email** or **SMS** (selectable via environment)
- Auto-generate pickup codes
- Pharmacist dispense flow with audit tracking
- Export dispensed-prescription report to CSV
- Full CLI-driven workflow

---

## 2. Technology Stack

| Component | Technology |
|----------|------------|
| Language | Python 3.8 |
| Database | PostgreSQL (NeonDB) |
| QR Code API | https://api.qrserver.com/v1/create-qr-code/ |
| DB Driver | psycopg2-binary |
| CLI | Pure Python (no frameworks) |
| Patterns Used | Command, Repository, Factory Method |

---

## 3. Environment Configuration

| Variable | Purpose | Example |
|---------|---------|---------|
| HP_DB_DSN | Database connection | postgresql://user:pass@host/db |
| HP_NOTIFY_TYPE | Notification channel | email or sms |

Example:
```
export HP_DB_DSN="postgresql://..."
export HP_NOTIFY_TYPE=email
```

---

## 4. Installation & Running

### Step 1: Create environment
```
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install dependencies
```
python -m pip install -r requirements.txt
```

### Step 3: Set environment variables
```
export HP_DB_DSN="postgresql://..."
export HP_NOTIFY_TYPE=email   # or sms
```

### Step 4: Run the application
```
python main.py
```

---

## 5. Application Structure
```
healthpass/
 ├── main.py
 ├── console_cli.py
 ├── command.py
 ├── notifier.py
 ├── repositories.py
 ├── services/
 │    ├── patient_service.py
 │    ├── prescription_service.py
 │    ├── qr_service.py
 ├── models.py
 ├── db.py
 ├── config.py
 ├── README.md
 └── requirements.txt
```

---

## 6. Design Patterns

### Command Pattern
Used for:
- AddPatientCommand
- NewPrescriptionCommand
- GeneratePickupQRCommand
- DispensePrescriptionCommand
- ReportDispensedCommand

### Repository Pattern
Used for DB access:
- PatientRepo  
- PrescriptionRepo  
- AuditRepo  

### Factory Method
Selects:
- EmailNotifier  
- SMSNotifier  
via `HP_NOTIFY_TYPE`.

---

## 7. Notifications Workflow

- Pharmacist selects notify option  
- Missing email/phone triggers prompt and DB update  
- Pharmacist chooses whether to attach QR  
- System ensures pickup code + QR exist  
- Factory chooses notifier  
- Notification simulated in console  
- Logged in audit_log  

---

## 8. Reporting Workflow

- Shows dispensed prescriptions  
- CSV export to:
```
reports/dispensed_prescriptions.csv
```
- Overwrites previous file  

---

## 9. Third-Party Integration

QR API endpoint:
```
https://api.qrserver.com/v1/create-qr-code/
```
Local storage:
```
qr_codes/prescription_<id>_<code>.png
```

---

## 10. Running Locally (For Markers)
```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export HP_DB_DSN="postgresql://....."
export HP_NOTIFY_TYPE=email
python main.py
```

---

## 11. Licence

Academic submission for:
SFWRTECH 4SA3 – Software Architecture (McMaster University)
```
