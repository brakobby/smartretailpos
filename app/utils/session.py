"""
SmartRetail POS — Session Manager

A simple singleton that holds the currently authenticated user.
All modules check this to know who is logged in and what role they hold.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional


class _Session:
    """Application-level authentication session."""

    def __init__(self):
        self._user_id:   Optional[int] = None
        self._username:  Optional[str] = None
        self._full_name: Optional[str] = None
        self._role:      Optional[str] = None
        self._login_time: Optional[datetime] = None

    # ── Login / Logout ────────────────────────────────────────────────────────

    def login(self, user_id: int, username: str, full_name: str, role: str) -> None:
        self._user_id    = user_id
        self._username   = username
        self._full_name  = full_name
        self._role       = role
        self._login_time = datetime.now()

    def logout(self) -> None:
        self._user_id    = None
        self._username   = None
        self._full_name  = None
        self._role       = None
        self._login_time = None

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_authenticated(self) -> bool:
        return self._user_id is not None

    @property
    def user_id(self) -> Optional[int]:
        return self._user_id

    @property
    def username(self) -> Optional[str]:
        return self._username

    @property
    def full_name(self) -> Optional[str]:
        return self._full_name

    @property
    def role(self) -> Optional[str]:
        return self._role

    @property
    def login_time(self) -> Optional[datetime]:
        return self._login_time

    # ── Permission Checks ─────────────────────────────────────────────────────

    def has_permission(self, permission: str) -> bool:
        """Check if the current user has a specific permission key."""
        if not self.is_authenticated:
            return False
        from app.config.settings import PERMISSIONS
        allowed = PERMISSIONS.get(self._role, [])
        return permission in allowed

    def is_admin(self) -> bool:
        from app.config.settings import ROLE_ADMIN
        return self._role == ROLE_ADMIN

    def is_manager_or_above(self) -> bool:
        from app.config.settings import ROLE_ADMIN, ROLE_MANAGER
        return self._role in (ROLE_ADMIN, ROLE_MANAGER)

    def __repr__(self):
        return f"<Session user={self._username} role={self._role}>"


# ── Singleton instance ────────────────────────────────────────────────────────
current_session = _Session()
