
import json
import math
import os
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal
from .models import Analysis
from .schemas import AnalyzeRequest, AnalyzeResponse, AnalysisPayload, SearchResponse
from .keywords import extract_keywords
from .llm import analyze_with_llm, LLMError

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLM Knowledge Extractor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def confidence_score(text: str, keywords: List[str]) -> float:
    # Naive heuristic: combine text length and number of keywords
    length_factor = min(1.0, len(text) / 1200.0)  # caps at ~1200 chars
    keyword_factor = min(1.0, len(set(keywords)) / 3.0)
    score = 0.6 * length_factor + 0.4 * keyword_factor
    return round(score, 2)

def _persist_analysis(db: Session, input_text: str, summary: str, meta: dict, keywords: List[str]) -> Analysis:
    obj = Analysis(
        title=meta.get("title"),
        summary=summary,
        sentiment=meta.get("sentiment"),
        topics=json.dumps(meta.get("topics", [])),
        keywords=json.dumps(keywords),
        input_text=input_text,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def _to_payload(a: Analysis) -> AnalysisPayload:
    topics = json.loads(a.topics or "[]")
    keywords = json.loads(a.keywords or "[]")
    return AnalysisPayload(
        id=a.id,
        title=a.title,
        summary=a.summary,
        sentiment=a.sentiment,
        topics=topics,
        keywords=keywords,
        confidence=confidence_score(a.input_text, keywords),
    )

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    # Edge case: no content
    texts: List[str] = []
    if req.text and req.text.strip():
        texts = [req.text.strip()]
    elif req.texts and isinstance(req.texts, list):
        texts = [t.strip() for t in req.texts if isinstance(t, str) and t.strip()]
    if not texts:
        raise HTTPException(status_code=400, detail="Input text is empty. Provide 'text' or non-empty 'texts'.")

    results = []
    for t in texts:
        try:
            llm_out = analyze_with_llm(t)
        except LLMError as e:
            # Edge case: LLM failure
            raise HTTPException(status_code=502, detail=f"Analysis failed: {e}")

        summary = llm_out.get("summary") or ""
        meta = llm_out.get("meta") or {"title": None, "topics": [], "sentiment": "neutral"}
        # Ensure topics present and normalized
        topics = meta.get("topics") or []
        topics = [str(x).strip() for x in topics][:3]

        # Implement keywords ourselves (no LLM)
        kws = extract_keywords(t, top_k=3)

        # Persist
        row = _persist_analysis(db, t, summary, {**meta, "topics": topics}, kws)
        results.append(_to_payload(row))

    return AnalyzeResponse(results=results)

@app.get("/search", response_model=SearchResponse)
def search(topic: str = Query(..., description="Topic or keyword to search"),
           db: Session = Depends(get_db)):
    q = f"%{topic.lower()}%"
    rows = db.query(Analysis).filter(
        (Analysis.topics.ilike(q)) | (Analysis.keywords.ilike(q))
    ).order_by(Analysis.created_at.desc()).all()
    return SearchResponse(results=[_to_payload(r) for r in rows])
