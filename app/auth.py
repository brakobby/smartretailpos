"""
Authentication and user management
"""
import bcrypt
from datetime import datetime
from .database import User, AuditLog, SessionLocal

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def authenticate(username: str, password: str):
    """Authenticate user and return user info or None"""
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username, is_active=True).first()
        if user and verify_password(password, user.password_hash):
            # Log the login
            log = AuditLog(
                user_id=user.id,
                action="LOGIN",
                details=f"User {username} logged in",
                timestamp=datetime.now()
            )
            session.add(log)
            session.commit()
            
            return {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role
            }
        return None
    except Exception as e:
        session.rollback()
        print(f"Authentication error: {e}")
        return None
    finally:
        session.close()

def create_user(username: str, password: str, full_name: str, role: str) -> bool:
    """Create a new user"""
    session = SessionLocal()
    try:
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            return False
        
        user = User(
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role
        )
        session.add(user)
        session.commit()
        return True
    except:
        session.rollback()
        return False
    finally:
        session.close()

def get_all_users():
    """Get all active users"""
    session = SessionLocal()
    try:
        return session.query(User).filter_by(is_active=True).all()
    finally:
        session.close()

def update_user(user_id: int, **kwargs):
    """Update user details"""
    session = SessionLocal()
    try:
        user = session.query(User).get(user_id)
        if user:
            if 'password' in kwargs:
                kwargs['password_hash'] = hash_password(kwargs.pop('password'))
            for key, value in kwargs.items():
                setattr(user, key, value)
            session.commit()
            return True
        return False
    except:
        session.rollback()
        return False
    finally:
        session.close()

def delete_user(user_id: int):
    """Soft delete a user"""
    return update_user(user_id, is_active=False)

def log_action(user_id: int, action: str, details: str = ""):
    """Log user actions"""
    session = SessionLocal()
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            timestamp=datetime.now()
        )
        session.add(log)
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()