import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import timedelta
from typing import Optional
from datetime import datetime
from db.database import Base
from enum import Enum as PyEnum

class ExtractionStatus(PyEnum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"

class UserDB(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)

    invoices = relationship("FileDB", back_populates="owner")

class FileDB(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("UserDB", back_populates="invoices")
    extracted_file = relationship("ExtractedFileDB", back_populates="file", uselist=False, cascade="all, delete-orphan")

class ExtractedFileDB(Base):
    __tablename__ = "extracted_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)
    extracted_text = Column(Text, nullable=True)
    json_data = Column(JSONB, nullable=True)
    status = Column(Enum(ExtractionStatus), default=ExtractionStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text, nullable=True)

    file = relationship("FileDB", back_populates="extracted_file")