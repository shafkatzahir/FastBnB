from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import bcrypt
from jose import jwt, JWTError

from .. import schemas, crud, auth, models
from ..auth import create_refresh_token
from ..database import get_db
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

def hash_refresh_token(token: str) -> str:
    return bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_refresh_token(plain_token: str, hashed_token: str) -> bool:
    return bcrypt.checkpw(plain_token.encode('utf-8'), hashed_token.encode('utf-8'))



@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = auth.create_refresh_token(data={"sub": str(user.id)})

    user.refresh_token_hash = hash_refresh_token(refresh_token)
    db.commit()

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(
    response: Response,
    refresh_token: Annotated[Optional[str], Cookie()] = None,
    db: Session = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token cookie missing")

    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        user = db.query(models.User).filter(models.User.id == user_id).first()

        if not user or not user.refresh_token_hash or not verify_refresh_token(refresh_token, user.refresh_token_hash):
            raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

        new_access_token = auth.create_access_token(data={"sub": str(user.id), "role": user.role.value})
        new_refresh_token = create_refresh_token(data={"sub": user.id})
        new_refresh_token_hashed = hash_refresh_token(new_refresh_token)

        # 4. Update the stored refresh token hash (token rotation)
        user.refresh_token_hash = new_refresh_token_hashed
        db.commit()

        # 5. Set the new refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )


        return {"access_token": new_access_token, "token_type": "bearer"}
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")


