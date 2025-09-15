
from typing import List, Optional, Union
from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    text: Optional[str] = Field(None, description="Single text to analyze")
    texts: Optional[List[str]] = Field(None, description="Batch texts to analyze (optional)")

class AnalysisPayload(BaseModel):
    id: int
    title: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    topics: List[str] = []
    keywords: List[str] = []
    confidence: float = 0.0

class AnalyzeResponse(BaseModel):
    results: List[AnalysisPayload]

class SearchResponse(BaseModel):
    results: List[AnalysisPayload]

