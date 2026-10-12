from fastapi import APIRouter, Depends, HTTPException, Response, status
from security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, verify_password
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import SignupSchema, LoginSchema, UserResponseSchema
from dependancies import get_current_user
from schemas import UserResponseSchema

router = APIRouter()
@router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
def register_user(user_data: SignupSchema,db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email = user_data.email,
        username = user_data.username,
        first = user_data.first,
        last = user_data.last,
        password_hash = hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login_user(user_data: LoginSchema, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token({"sub": str(user.id)})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"message": "Logged in"}

@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out"}

@router.get("/me", response_model=UserResponseSchema)
def get_current_user(current_user: User = Depends(get_current_user)):
    return current_user