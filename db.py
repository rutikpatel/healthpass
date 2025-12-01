import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DSN = "postgresql://neondb_owner:npg_zNfpcEK4xbm3@ep-flat-lake-a4rd4uww-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def get_connection():
    return psycopg2.connect(DSN)


@contextmanager
def db_cursor(dict_cursor: bool = True):
    conn = get_connection()
    try:
        cursor_factory = RealDictCursor if dict_cursor else None
        cur = conn.cursor(cursor_factory=cursor_factory)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Initializes the database schema for the vertical slice. Uses IF NOT EXISTS so
# it is safe to call on every startup.
def init_schema():
    """Create minimal tables for the first vertical slice."""
    ddl = """
    CREATE TABLE IF NOT EXISTS patients (
        id              SERIAL PRIMARY KEY,
        health_card_no  VARCHAR(64) UNIQUE NOT NULL,
        first_name      VARCHAR(100) NOT NULL,
        last_name       VARCHAR(100) NOT NULL,
        date_of_birth   DATE NOT NULL,
        phone           VARCHAR(30),
        email           VARCHAR(255),
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS prescriptions (
        id              SERIAL PRIMARY KEY,
        patient_id      INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        drug_name       VARCHAR(255) NOT NULL,
        dosage          VARCHAR(255) NOT NULL,
        instructions    TEXT,
        status          VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
        pickup_code     VARCHAR(64) UNIQUE,
        pickup_qr_path  TEXT,
        expires_at      TIMESTAMPTZ,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        picked_up_at    TIMESTAMPTZ
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        id          SERIAL PRIMARY KEY,
        event_type  VARCHAR(64) NOT NULL,
        payload     TEXT        NOT NULL,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    with db_cursor(dict_cursor=False) as cur:
        cur.execute(ddl)

