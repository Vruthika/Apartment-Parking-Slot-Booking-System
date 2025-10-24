from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.utils.auth_utils import verify_token
from app.crud.user_crud import get_user_by_email

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token_data = verify_token(credentials.credentials)
    user = get_user_by_email(db, email=token_data["email"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user

def get_current_admin(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required.",
        )
    return current_user

def get_current_resident(current_user = Depends(get_current_user)):
    if current_user.role != "resident":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Resident access required.",
        )
    return current_user