import os
import uuid
import json
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from pydantic import BaseModel
from cryptography.fernet import Fernet, InvalidToken

from db.database import Base
from db.table_models import ExtractedFileDB, FileDB, ExtractionStatus
from models.invoice_extraction_model import (
    preprocess_image_for_ocr, 
    extract_text_from_image,
    extract_fields_with_llm,
    extract_fields_with_regex
)
from auth.encryption import get_user_fernet_key 

TMP_DECRYPTED_DIR = "tmp/decrypted"
TMP_PROCESSED_DIR = "tmp/processed"

os.makedirs(TMP_DECRYPTED_DIR, exist_ok=True)
os.makedirs(TMP_PROCESSED_DIR, exist_ok=True)


class ExtractedFileResponse(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    extracted_text: Optional[str]
    json_data: Optional[dict]
    status: str
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str]

    class Config:
        from_attributes = True


def decrypt_file(encrypted_path: str, decrypted_path: str, fernet: Fernet):
    with open(encrypted_path, "rb") as f:
        encrypted_data = f.read()

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except InvalidToken:
        raise ValueError("Invalid decryption key or corrupted file.")

    with open(decrypted_path, "wb") as f:
        f.write(decrypted_data)


def extract_text_and_entities(encrypted_path: str, fernet: Fernet) -> Tuple[str, dict, Optional[str], str, str]:
    filename = os.path.basename(encrypted_path)
    decrypted_path = os.path.join(TMP_DECRYPTED_DIR, filename)
    processed_path = os.path.join(TMP_PROCESSED_DIR, filename)

    if not os.path.exists(encrypted_path):
        raise FileNotFoundError("Encrypted file not found")

    decrypt_file(encrypted_path, decrypted_path, fernet)
    preprocess_image_for_ocr(decrypted_path, processed_path)

    extracted_text = extract_text_from_image(processed_path)
    if not extracted_text:
        return "OCR error", {}, "", decrypted_path, processed_path

    json_data = extract_fields_with_llm(extracted_text)
    if "error" in json_data:
        fallback_data = extract_fields_with_regex(extracted_text)
        return extracted_text, fallback_data, json_data["error"], decrypted_path, processed_path
    else:
        return extracted_text, json_data, None, decrypted_path, processed_path


def run_extraction(db: Session, user, file_id: uuid.UUID) -> ExtractedFileDB | None:
    file = db.query(FileDB).filter(FileDB.id == file_id, FileDB.user_id == user.id).first()
    if not file:
        return None

    extraction = db.query(ExtractedFileDB).filter(ExtractedFileDB.file_id == file_id).first()
    if not extraction:
        return None

    extraction.status = ExtractionStatus.processing
    db.commit()

    decrypted_path = None
    processed_path = None

    try:
        fernet_key = get_user_fernet_key(user.username)
        fernet = Fernet(fernet_key)

        extracted_text, json_data, llm_error, decrypted_path, processed_path = extract_text_and_entities(file.path, fernet)
        if extracted_text == "OCR error":
            print("OCR extraction failed, setting extraction status to error.")
            extraction.status = ExtractionStatus.error
            extraction.error_message = "ocr_error"
            db.commit()
            return extraction

        extraction.extracted_text = extracted_text
        extraction.json_data = json_data
        extraction.status = ExtractionStatus.done

        if llm_error:
            extraction.error_message = f"LLM failed, regex fallback used: {llm_error}"

    except Exception as e:
        print(f"Error during extraction: {e}")
        extraction.status = ExtractionStatus.error
        extraction.error_message = str(e)

    finally:
        # Cleanup decrypted and processed files
        for path in [decrypted_path, processed_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_error:
                    print(f"Warning: Failed to clean up temp file {path}: {cleanup_error}")

    db.commit()
    db.refresh(extraction)
    return extraction