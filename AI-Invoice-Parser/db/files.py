import os
import uuid
import base64
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from enum import Enum

from config import LOCAL_STORAGE_DIR
from db.database import Base
from db.extracted import ExtractedFileDB, ExtractionStatus
from db.table_models import FileDB
from auth.encryption import get_user_fernet_key

from pydantic import BaseModel

class fileType(Enum):
    pdf = "pdf"
    png = "png"
    jpg = "jpg"

# Pydantic Models
class FileResponse(BaseModel):
    id: uuid.UUID
    filename: str
    filetype: fileType
    path: str

    class Config:
        from_attributes = True

class DecryptedFileResponse(BaseModel):
    filename: str
    content_base64: str
    filetype: fileType

    class Config:
        from_attributes = True

def save(db: Session, user, uploaded_file) -> FileResponse:
    file_data = uploaded_file.file.read()
    fernet = Fernet(get_user_fernet_key(user.username))

    encrypted_data = fernet.encrypt(file_data)

    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{uploaded_file.filename}"
    full_path = os.path.join(LOCAL_STORAGE_DIR, filename)

    with open(full_path, "wb") as f:
        f.write(encrypted_data)

    new_file = FileDB(
        id=file_id,
        user_id=user.id,
        filename=uploaded_file.filename,
        path=full_path,
    )
    db.add(new_file)

    db.add(ExtractedFileDB(file_id=file_id, status=ExtractionStatus.pending))
    db.commit()
    db.refresh(new_file)

    return FileResponse(
        id=new_file.id,
        filename=new_file.filename,
        filetype=fileType(new_file.filename.split('.')[-1].lower()),
        path=new_file.path
    )

def list(db: Session, user) -> list[FileDB]:
    files =  db.query(FileDB).filter(FileDB.user_id == user.id).all()
    return [
        FileResponse(
            id=f.id,
            filename=f.filename,
            path=f.path,
            filetype=fileType(f.filename.split(".")[-1].lower())
        )
        for f in files
    ]

def get(db: Session, user, file_id: uuid.UUID) -> DecryptedFileResponse:
    file = db.query(FileDB).filter(FileDB.id == file_id, FileDB.user_id == user.id).first()
    if not file:
        return None

    fernet = Fernet(get_user_fernet_key(user.username))
    with open(file.path, "rb") as f:
        encrypted_data = f.read()

    try:
        decrypted = fernet.decrypt(encrypted_data)
    except Exception:
        return None

    return DecryptedFileResponse(
        filename=file.filename,
        content_base64=base64.b64encode(decrypted).decode("utf-8"),
        filetype=fileType(file.filename.split('.')[-1].lower())
    )

def delete(db: Session, user, file_id: uuid.UUID) -> bool:
    file = db.query(FileDB).filter(FileDB.id == file_id, FileDB.user_id == user.id).first()
    if not file:
        return False

    if os.path.exists(file.path):
        os.remove(file.path)

    db.delete(file)
    db.commit()
    return True

def delete_all(db: Session, user) -> int:
    files = db.query(FileDB).filter(FileDB.user_id == user.id).all()
    count = 0
    for file in files:
        if os.path.exists(file.path):
            os.remove(file.path)
        db.delete(file)
        count += 1
    db.commit()
    return count
