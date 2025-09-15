
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .db import Base

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    sentiment = Column(String(16), nullable=True, index=True)
    topics = Column(Text, nullable=True)     # JSON-encoded list[str]
    keywords = Column(Text, nullable=True)   # JSON-encoded list[str]
    input_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
