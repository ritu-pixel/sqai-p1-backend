import uuid
from pydantic import BaseModel
import bcrypt
from auth.jwt_handler import create_access_token
from db.table_models import UserDB

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# class LoginResponse(BaseModel):
#     id: uuid.UUID
#     username: str
#     access_token: TokenResponse

#     class Config:
#         from_attributes = True

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str

    class Config:
        from_attributes = True


def create(db, username: str, password: str) -> UserResponse:
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # FIXED
    new_user = UserDB(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
    )

def verify(db, username: str, password: str):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user and bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        return user
    return None

def get_by_username(db, username: str):
    return db.query(UserDB).filter(UserDB.username == username).first()