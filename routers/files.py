import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from auth.dependencies import get_current_user
from db.files import (
    FileResponse,
    DecryptedFileResponse,
    get,
    save,
    list,
    delete,
    # delete_all,
)

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=FileResponse)
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):  
    if file.content_type not in ["image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF, PNG, and JPG are allowed.",
        )
    return save(db, current_user, file)

@router.get("/", response_model=List[FileResponse])
def get_files(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list(db, current_user)

@router.get("/{file_id}", response_model=DecryptedFileResponse)
def get_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get(db, current_user, file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File not found or decryption failed")
    return result

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not delete(db, current_user, file_id):
        raise HTTPException(status_code=404, detail="File not found")
    return

# @router.delete("/everything", response_model=dict)
# def delete_all_files(
#     db: Session = Depends(get_db),
#     current_user=Depends(get_current_user),
# ):
#     count = delete_all(db, current_user)
#     return {"deleted": count}
