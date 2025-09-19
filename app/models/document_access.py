# app/models/document_access.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class DocumentAccess(Base):
    __tablename__ = "document_access"

    id = Column(Integer, primary_key=True, index=True)

    # keep the old column name "doc_id" because some code used it
    doc_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))

    # keep user_id because other code expects it (nullable - role-based access will set role instead)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # who granted (nullable)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # role (nullable) - e.g. "HR Executive", "Manager"
    role = Column(String, nullable=True)

    # access level (view/edit/download) - default "view"
    access_level = Column(String, nullable=False, default="view")

    # relationships
    document = relationship("Document", back_populates="access_list")
    user = relationship("User", foreign_keys=[user_id], backref="document_accesses")
    granter = relationship("User", foreign_keys=[granted_by], backref="granted_document_accesses")
