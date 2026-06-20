"""
SmartRetail POS — Authentication Service

Handles:
  - authenticate(username, password) → User | None
  - change_password(user_id, old, new) → bool
  - create_user(...)
  - list_users()
  - toggle_user_status()
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from app.database.database import get_session
from app.database.models import Role, User, AuditLog, UserStatus
from app.utils.helpers import hash_password, verify_password
from app.utils.session import current_session

logger = logging.getLogger(__name__)


class AuthService:

    # ── Authentication ────────────────────────────────────────────────────────

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        """
        Validate credentials.
        Returns the User object on success, None on failure.
        Updates last_login timestamp on success.
        """
        with get_session() as session:
            user = (
                session.query(User)
                .filter_by(username=username.strip(), status=UserStatus.ACTIVE)
                .first()
            )
            if user is None:
                logger.warning("Login failed: unknown user '%s'", username)
                return None

            if not verify_password(password, user.password_hash):
                logger.warning("Login failed: wrong password for '%s'", username)
                AuthService._log_action(session, user.id, "LOGIN_FAILED",
                                        f"Failed login attempt for {username}")
                return None

            # Update last login
            user.last_login = datetime.utcnow()

            # Log the successful login
            AuthService._log_action(session, user.id, "LOGIN",
                                    f"User {username} logged in")

            # Populate session
            role_name = user.role.role_name if user.role else "Unknown"
            current_session.login(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                role=role_name,
            )

            logger.info("User '%s' authenticated successfully (role=%s)",
                        username, role_name)
            return user

    @staticmethod
    def logout() -> None:
        if current_session.is_authenticated:
            with get_session() as session:
                AuthService._log_action(
                    session, current_session.user_id,
                    "LOGOUT", f"User {current_session.username} logged out"
                )
        current_session.logout()

    # ── Password Management ───────────────────────────────────────────────────

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> bool:
        with get_session() as session:
            user = session.get(User, user_id)
            if user is None:
                return False
            if not verify_password(old_password, user.password_hash):
                return False
            if len(new_password) < 6:
                raise ValueError("Password must be at least 6 characters.")
            user.password_hash = hash_password(new_password)
            AuthService._log_action(session, user_id, "PASSWORD_CHANGE",
                                    f"Password changed for {user.username}")
            return True

    @staticmethod
    def reset_password(user_id: int, new_password: str) -> bool:
        """Admin can reset any user's password without knowing old one."""
        if not current_session.is_admin():
            raise PermissionError("Only admins can reset passwords.")
        with get_session() as session:
            user = session.get(User, user_id)
            if user is None:
                return False
            if len(new_password) < 6:
                raise ValueError("Password must be at least 6 characters.")
            user.password_hash = hash_password(new_password)
            AuthService._log_action(session, current_session.user_id,
                                    "PASSWORD_RESET",
                                    f"Admin reset password for {user.username}")
            return True

    # ── User Management ───────────────────────────────────────────────────────

    @staticmethod
    def create_user(username: str, password: str, full_name: str,
                    role_name: str) -> User:
        if not current_session.is_admin():
            raise PermissionError("Only administrators can create users.")
        with get_session() as session:
            existing = session.query(User).filter_by(username=username).first()
            if existing:
                raise ValueError(f"Username '{username}' is already taken.")
            role = session.query(Role).filter_by(role_name=role_name).first()
            if not role:
                raise ValueError(f"Role '{role_name}' does not exist.")
            user = User(
                username=username,
                password_hash=hash_password(password),
                full_name=full_name,
                role_id=role.id,
                status=UserStatus.ACTIVE,
            )
            session.add(user)
            session.flush()
            AuthService._log_action(session, current_session.user_id,
                                    "USER_CREATED", f"Created user {username}")
            return user

    @staticmethod
    def list_users() -> List[User]:
        with get_session() as session:
            return session.query(User).join(Role).all()

    @staticmethod
    def toggle_user_status(user_id: int) -> UserStatus:
        if not current_session.is_admin():
            raise PermissionError("Only administrators can change user status.")
        with get_session() as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError("User not found.")
            if user.id == current_session.user_id:
                raise ValueError("You cannot deactivate your own account.")
            user.status = (
                UserStatus.INACTIVE
                if user.status == UserStatus.ACTIVE
                else UserStatus.ACTIVE
            )
            AuthService._log_action(session, current_session.user_id,
                                    "USER_STATUS_CHANGE",
                                    f"Changed status for {user.username} → {user.status}")
            return user.status

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _log_action(session, user_id: Optional[int], action: str,
                    details: str = "") -> None:
        log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            module="AUTH",
        )
        session.add(log)
