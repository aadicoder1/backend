# app/models/document.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    department = Column(String, nullable=True)
    access_role = Column(String, nullable=True)  # (optional: keep or remove if using fine-grained access)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
    access_list = relationship("DocumentAccess", back_populates="document", cascade="all, delete-orphan")
