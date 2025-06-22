import os
from dotenv import load_dotenv

load_dotenv()

JWT_KEY = os.getenv("JWT_KEY", "your_super_secret_key")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin123@localhost:5432/invoicedb")
LOCAL_STORAGE_DIR = os.getenv("LOCAL_STORAGE_DIR", "invoices_data")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY","dummy_key_for_no_op")
TESSERACT_CMD = os.getenv("TESSERACT_CMD",r"C://Program Files//Tesseract-OCR//tesseract.exe")