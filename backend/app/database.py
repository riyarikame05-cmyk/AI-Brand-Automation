from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


# =========================================================
# PATHS + ENVIRONMENT
# =========================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(ENV_PATH)


# =========================================================
# CONFIGURATION
# =========================================================

DATABASE_PROVIDER = (
    os.getenv("DATABASE_PROVIDER", "auto")
    .strip()
    .lower()
)

DATABASE_URL = (
    os.getenv("DATABASE_URL", "")
    .strip()
)

LOCAL_DATABASE_FILE = (
    BACKEND_DIR / "brandai_local.db"
)

LOCAL_DATABASE_URL = os.getenv(
    "LOCAL_DATABASE_URL",
    f"sqlite:///{LOCAL_DATABASE_FILE.as_posix()}",
).strip()

SUPPORTED_PROVIDERS = {
    "auto",
    "supabase",
    "postgres",
    "postgresql",
    "local",
    "sqlite",
}


if DATABASE_PROVIDER not in SUPPORTED_PROVIDERS:
    print(
        f"[DATABASE] Unknown provider "
        f"'{DATABASE_PROVIDER}'. Using auto."
    )
    DATABASE_PROVIDER = "auto"


# =========================================================
# SQLITE CONNECTION CONFIGURATION
# =========================================================

def configure_sqlite_connection(
    dbapi_connection,
    connection_record,
) -> None:
    """
    Configure every SQLite connection for better local concurrency.

    WAL allows readers to continue while another connection writes.
    busy_timeout makes SQLite wait for a short-lived writer rather
    than immediately raising "database is locked".
    """

    cursor = dbapi_connection.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
    finally:
        cursor.close()


# =========================================================
# ENGINE FACTORIES
# =========================================================

def create_remote_engine() -> Engine:
    """
    Create the PostgreSQL/Supabase engine.

    Connectivity is tested separately before this engine is
    selected for the backend process.
    """

    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL is not configured."
        )

    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 5,
        },
    )


def create_local_engine() -> Engine:
    """
    Create the offline SQLite engine.
    """

    local_engine = create_engine(
        LOCAL_DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
        },
        pool_pre_ping=True,
    )

    event.listen(
        local_engine,
        "connect",
        configure_sqlite_connection,
    )

    return local_engine


# =========================================================
# CONNECTION TEST
# =========================================================

def database_is_available(
    candidate_engine: Engine,
) -> bool:
    try:
        with candidate_engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        return True

    except Exception as error:
        print(
            "[DATABASE] Connection test failed:",
            repr(error),
        )

        try:
            candidate_engine.dispose()
        except Exception:
            pass

        return False


# =========================================================
# DATABASE SELECTION
# =========================================================

def select_engine() -> tuple[Engine, str]:
    """
    Choose exactly one database for this backend process.

    auto:
        Supabase/PostgreSQL
              |
              | unavailable
              v
        SQLite

    The selected database never changes in the middle of
    individual requests.
    """

    # -----------------------------------------------------
    # Explicit local mode
    # -----------------------------------------------------

    if DATABASE_PROVIDER in {
        "local",
        "sqlite",
    }:
        print(
            "[DATABASE] Local database mode requested."
        )

        return (
            create_local_engine(),
            "sqlite",
        )

    # -----------------------------------------------------
    # Explicit remote mode
    # -----------------------------------------------------

    if DATABASE_PROVIDER in {
        "supabase",
        "postgres",
        "postgresql",
    }:
        print(
            "[DATABASE] Supabase/PostgreSQL "
            "mode requested."
        )

        remote_engine = create_remote_engine()

        if not database_is_available(
            remote_engine
        ):
            raise RuntimeError(
                "Supabase/PostgreSQL is unavailable "
                "and DATABASE_PROVIDER is configured "
                "for remote-only operation."
            )

        print(
            "[DATABASE] Using Supabase/PostgreSQL."
        )

        return (
            remote_engine,
            "postgresql",
        )

    # -----------------------------------------------------
    # Automatic hybrid mode
    # -----------------------------------------------------

    print(
        "[DATABASE] Auto mode."
    )

    if DATABASE_URL:
        try:
            remote_engine = create_remote_engine()

            print(
                "[DATABASE] Testing "
                "Supabase/PostgreSQL..."
            )

            if database_is_available(
                remote_engine
            ):
                print(
                    "[DATABASE] Using "
                    "Supabase/PostgreSQL."
                )

                return (
                    remote_engine,
                    "postgresql",
                )

        except Exception as error:
            print(
                "[DATABASE] Remote database "
                "initialization failed:",
                repr(error),
            )

    else:
        print(
            "[DATABASE] DATABASE_URL is not configured."
        )

    print(
        "[DATABASE] Supabase unavailable. "
        "Using local SQLite fallback."
    )

    return (
        create_local_engine(),
        "sqlite",
    )


# =========================================================
# ACTIVE DATABASE
# =========================================================

engine, ACTIVE_DATABASE = select_engine()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


# =========================================================
# LOCAL TABLE INITIALIZATION
# =========================================================

def initialize_local_database() -> None:
    """
    Create tables only when SQLite is the selected database.
    """

    if ACTIVE_DATABASE != "sqlite":
        return

    try:
        from .models import Base

        Base.metadata.create_all(
            bind=engine
        )

        # Force one connection so the SQLite PRAGMAs above
        # are applied and WAL is initialized immediately.
        with engine.connect() as connection:
            journal_mode = connection.execute(
                text("PRAGMA journal_mode")
            ).scalar()

            busy_timeout = connection.execute(
                text("PRAGMA busy_timeout")
            ).scalar()

        print(
            "[DATABASE] Local SQLite tables ready."
        )
        print(
            f"[DATABASE] Local file: "
            f"{LOCAL_DATABASE_FILE}"
        )
        print(
            f"[DATABASE] SQLite journal mode: "
            f"{journal_mode}"
        )
        print(
            f"[DATABASE] SQLite busy timeout: "
            f"{busy_timeout} ms"
        )

    except ImportError as error:
        raise RuntimeError(
            "SQLite fallback was selected, but SQLAlchemy Base "
            "could not be imported from app.models. "
            "The model metadata must be available before local "
            "tables can be created."
        ) from error


initialize_local_database()


# =========================================================
# FASTAPI DEPENDENCY
# =========================================================

def get_db() -> Generator[
    Session,
    None,
    None,
]:
    db = SessionLocal()

    try:
        yield db

    except SQLAlchemyError:
        db.rollback()
        raise

    finally:
        db.close()


# =========================================================
# STATUS HELPER
# =========================================================

def get_database_status() -> dict:
    return {
        "provider": ACTIVE_DATABASE,
        "online": (
            ACTIVE_DATABASE == "postgresql"
        ),
        "local_file": (
            str(LOCAL_DATABASE_FILE)
            if ACTIVE_DATABASE == "sqlite"
            else None
        ),
    }