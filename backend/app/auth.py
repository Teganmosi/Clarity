"""
Authentication module for API key and user management
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets
import os
from dotenv import load_dotenv

from .database import get_db
from .models import User

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
API_KEY_HEADER = "X-API-Key"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    return pwd_context.hash(password)


def generate_api_key() -> str:
    """
    Generate a secure random API key
    """
    return f"lsk_{secrets.token_urlsafe(32)}"


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user_by_api_key(
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user by API key
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    user = db.query(User).filter(User.api_key == api_key, User.is_active == True).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return user


async def get_current_user_by_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user by JWT token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(credentials.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user(
    api_key: str = Depends(api_key_header),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user using either API key or JWT token
    """
    # Try API key first
    if api_key:
        user = db.query(User).filter(User.api_key == api_key, User.is_active == True).first()
        if user:
            return user
    
    # Try JWT token
    if credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            username: str = payload.get("sub")
            if username:
                user = db.query(User).filter(User.username == username, User.is_active == True).first()
                if user:
                    return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_user(db: Session, username: str, email: str, password: str = None) -> User:
    """
    Create a new user
    """
    # Generate API key
    api_key = generate_api_key()
    
    # Hash password if provided
    hashed_password = get_password_hash(password) if password else None
    
    # Create user
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        api_key=api_key
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    """
    Authenticate user with username and password
    """
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
    
    # If user has a hashed password, verify it
    if user.hashed_password:
        if not verify_password(password, user.hashed_password):
            return None
    else:
        # For backward compatibility with users created without passwords
        # Allow authentication but log a warning
        import logging
        logging.warning(f"User {username} has no password set. Consider setting one for security.")
    
    return user


def verify_admin_key(api_key: str) -> bool:
    """
    Verify if the API key is an admin key
    """
    admin_key = os.getenv("ADMIN_API_KEY", "")
    return api_key == admin_key
