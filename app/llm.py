
import json
import os
from typing import Dict, Any

class LLMError(Exception):
    pass

def _build_prompt(text: str) -> str:
    return f"""You are a precise information extractor.
Given the following text, produce:
1) A 1–2 sentence summary.
2) A compact JSON with: title (if available), topics (3 key topics), sentiment (positive/neutral/negative).

Text:
---
{text}
---

Respond EXACTLY in the following format:
SUMMARY: <one or two sentences>
JSON: {"title": "...", "topics": ["t1","t2","t3"], "sentiment": "neutral"}"""

def call_openai(text: str) -> Dict[str, Any]:
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise LLMError("OpenAI SDK not installed. Set LLM_MODE=mock or install 'openai'.") from e

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("OPENAI_API_KEY is not set")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    prompt = _build_prompt(text)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role":"user","content":prompt}],
            temperature=0.2,
        )
        content = resp.choices[0].message.content.strip()
    except Exception as e:
        raise LLMError(f"LLM call failed: {e}") from e

    # Parse the response
    summary = None
    j = None
    try:
        # Expected "SUMMARY: ..." and "JSON: {...}"
        parts = content.split("JSON:", 1)
        summary_line = parts[0].strip()
        if summary_line.upper().startswith("SUMMARY"):
            summary = summary_line.split(":",1)[1].strip()
        else:
            summary = summary_line.strip()
        j = json.loads(parts[1].strip())
    except Exception as e:
        # Try a looser fallback: attempt to find the last { ... } block
        try:
            start = content.rfind("{")
            end = content.rfind("}")
            j = json.loads(content[start:end+1])
        except Exception:
            raise LLMError(f"Could not parse LLM output: {content}") from e

    return {"summary": summary, "meta": j}

def call_mock(text: str) -> Dict[str, Any]:
    # Very small deterministic mock for tests and local dev
    first_period = text.find(".")
    snippet = text[: first_period+1] if first_period != -1 else text[:120]
    summary = snippet.strip() or "No content."
    topics = []
    if "ai" in text.lower(): topics.append("AI")
    if "cloud" in text.lower(): topics.append("Cloud")
    if "data" in text.lower(): topics.append("Data")
    while len(topics) < 3: topics.append("General")
    meta = {"title": None, "topics": topics[:3], "sentiment": "neutral"}
    return {"summary": summary, "meta": meta}

def analyze_with_llm(text: str) -> Dict[str, Any]:
    mode = os.getenv("LLM_MODE", "openai").lower()
    if mode == "mock":
        return call_mock(text)
    return call_openai(text)
