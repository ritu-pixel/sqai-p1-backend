import pytesseract
from cryptography.fernet import Fernet
from pdf2image import convert_from_bytes
from PIL import Image
import io
import os

from auth.encryption import get_user_fernet_key


def decrypt_file(path: str, fernet_key: bytes) -> bytes:
    with open(path, "rb") as f:
        encrypted_data = f.read()
    return Fernet(fernet_key).decrypt(encrypted_data)


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    images = convert_from_bytes(pdf_bytes)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text


def extract_text(path: str, filename: str, username: str) -> str:
    fernet_key = get_user_fernet_key(username)
    file_ext = os.path.splitext(filename)[-1].lower()

    decrypted_bytes = decrypt_file(path, fernet_key)

    if file_ext == ".pdf":
        return extract_text_from_pdf_bytes(decrypted_bytes)
    elif file_ext in [".png", ".jpg", ".jpeg"]:
        return extract_text_from_image_bytes(decrypted_bytes)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")
