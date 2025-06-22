from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from db.database import get_db
from db import extracted
from db.extracted import ExtractedFileResponse
from db.table_models import ExtractedFileDB, FileDB, ExtractionStatus
from auth.dependencies import get_current_user

router = APIRouter(prefix="/extract", tags=["Extraction"])

@router.post("/{file_id}", response_model=ExtractedFileResponse)
def extract_file(
    file_id: str,
    force: bool = Query(default=False, description="Force re-extraction even if already done."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    existing = (
        db.query(ExtractedFileDB)
        .join(FileDB, ExtractedFileDB.file_id == FileDB.id)
        .filter(and_(
            FileDB.user_id == user.id,
            ExtractedFileDB.file_id == file_id
        ))
        .first()
    )
    if existing and existing.status == ExtractionStatus.done and not force:
        print("Returning Existing")
        return existing

    # Run fresh extraction
    result = extracted.run_extraction(db, user, file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File not found or not authorized.")
    return result
