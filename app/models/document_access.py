# app/models/document_access.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class DocumentAccess(Base):
    __tablename__ = "document_access"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("documents.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    granted_by = Column(Integer, ForeignKey("users.id"))  # who gave access
    access_level = Column(String, default="view")  # view/edit/download

    document = relationship("Document", back_populates="access_list")
    user = relationship("User", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])
