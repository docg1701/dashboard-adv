from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector  # Import Vector type
from app.core.database import Base
from typing import List, Optional
from datetime import datetime

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False) # Assuming a reasonable length for hash
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Assuming a reasonable length for filename
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    # New columns for storing embeddings and a logical chunk ID from the transcriber service
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True) # Using Vector type
    logical_chunk_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True) # For the ID like "doc1_p1_c1"

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    # Optional: Add a unique constraint for logical_chunk_id per document
    # __table_args__ = (UniqueConstraint('document_id', 'logical_chunk_id', name='_document_logical_chunk_uc'),)
