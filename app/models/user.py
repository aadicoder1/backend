# app/models/user.py

from sqlalchemy import Column, Integer, String
from app.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)

    documents = relationship("Document", back_populates="user")
    document_access = relationship("DocumentAccess", back_populates="user", foreign_keys="DocumentAccess.user_id")
    granted_access = relationship("DocumentAccess", back_populates="granter", foreign_keys="DocumentAccess.granted_by")
