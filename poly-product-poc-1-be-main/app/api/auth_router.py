from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token
from app.dependencies.auth import get_current_user
from app.models.user_model import Token, UserCreate, UserLogin, UserOut
from app.services.user_service import UserService

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=Token)
def register(req: UserCreate):
    try:
        user_id = UserService.create_user(req.email, req.password)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    token = create_access_token({"sub": user_id, "email": req.email})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(req: UserLogin):
    user = UserService.authenticate(req.email, req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return UserOut(id=current_user["id"], email=current_user["email"])
