import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from backend.config.settings import settings
from backend.database.session import get_db
from backend.models.db_models import User
from backend.models.schema_models import TokenData

# Use standard OAuth2 schema reading token from headers (make optional to support query fallback)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    Generate a JWT token for user authentication.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(
    db: Session = Depends(get_db), 
    token: Optional[str] = Depends(oauth2_scheme),
    token_query: Optional[str] = None
) -> User:
    """
    Validate JWT token and retrieve current active user.
    Supports token retrieval via header or query parameters (fallback).
    """
    # For query parameters check, since we can't directly map FastAPI queries in routes unless declared,
    # let's look at authorization token parameter
    actual_token = token or token_query
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not actual_token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(actual_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        
        if email is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=user_id, role=role)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
        
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Validate that user has administrative privileges.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: requires administrator privileges"
        )
    return current_user
