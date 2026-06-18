import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.models.db_models import User
from backend.models.schema_models import UserRegister, UserLogin, UserOut, Token
from backend.utils.deps import create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    # Check if user email already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
        
    # Check if first user, make admin for analytics ease
    user_count = db.query(User).count()
    role = "admin" if user_count == 0 else "user"
    
    # Hash password and create user
    hashed_pwd = User.hash_password(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        role=role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token (Custom JSON Body).
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not user.verify_password(user_in.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Generate access token
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/swagger", response_model=Token, include_in_schema=False)
def login_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible login endpoint for Swagger documentation.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current logged in user details.
    """
    return current_user
