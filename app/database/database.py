"""
SmartRetail POS — Database Engine & Session Management

Provides:
  - get_engine()      — SQLAlchemy engine (singleton)
  - get_session()     — context-managed session
  - init_db()         — create all tables + seed default data
  - SessionLocal      — session factory for dependency injection
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import bcrypt
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import DATABASE_URL, ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER, ROLE_STOREKEEPER
from app.database.models import (
    Base, Role, User, Category, UserStatus,
)

logger = logging.getLogger(__name__)

# ── Engine (SQLite with WAL mode for performance) ─────────────────────────────

_engine = None


def get_engine():
    """Return the singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=False,  # Set True to see SQL queries during development
        )

        # Enable WAL journal mode and foreign keys on every connection
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    return _engine


# ── Session Factory ───────────────────────────────────────────────────────────

def _make_session_factory() -> sessionmaker:
    return sessionmaker(
        bind=get_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


SessionLocal: sessionmaker = None  # initialized on first call to init_db()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provide a transactional database session.

    Usage:
        with get_session() as session:
            products = session.query(Product).all()
    """
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = _make_session_factory()

    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Database Initialisation ───────────────────────────────────────────────────

def init_db() -> None:
    """
    Create all tables and populate seed data.
    Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS semantics.
    """
    global SessionLocal
    engine = get_engine()

    logger.info("Initialising database at %s", DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    SessionLocal = _make_session_factory()

    with get_session() as session:
        _seed_roles(session)
        _seed_default_admin(session)
        _seed_default_categories(session)

    logger.info("Database ready.")


# ── Seed Helpers ──────────────────────────────────────────────────────────────

def _seed_roles(session: Session) -> None:
    """Insert the four system roles if they do not already exist."""
    role_names = [ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER, ROLE_STOREKEEPER]
    existing = {r.role_name for r in session.query(Role).all()}
    for name in role_names:
        if name not in existing:
            session.add(Role(role_name=name))
    session.flush()


def _seed_default_admin(session: Session) -> None:
    """
    Create the default admin account if no users exist yet.
    Credentials: admin / admin123  (user MUST change this on first login)
    """
    if session.query(User).count() > 0:
        return  # Users already exist

    admin_role = session.query(Role).filter_by(role_name=ROLE_ADMIN).first()
    if not admin_role:
        return

    password_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
    admin = User(
        username="admin",
        password_hash=password_hash,
        full_name="System Administrator",
        role_id=admin_role.id,
        status=UserStatus.ACTIVE,
    )
    session.add(admin)
    session.flush()
    logger.info("Default admin user created. Username: admin | Password: admin123")


def _seed_default_categories(session: Session) -> None:
    """Create a handful of starter categories."""
    from app.database.models import Category

    defaults = [
        ("General",     "General merchandise"),
        ("Food & Beverages", "Consumables and drinks"),
        ("Electronics", "Electronic devices and accessories"),
        ("Clothing",    "Apparel and fashion"),
        ("Household",   "Household items and appliances"),
    ]
    existing = {c.name for c in session.query(Category).all()}
    for name, desc in defaults:
        if name not in existing:
            session.add(Category(name=name, description=desc))
    session.flush()
