
# LLM Knowledge Extractor

A tiny FastAPI service that accepts unstructured text and uses an LLM to produce a 1–2 sentence summary and structured metadata, plus **locally computed** keywords (the 3 most frequent nouns). Results are persisted in SQLite and searchable by topic/keyword.

---

## Local Environment Setup

1. Setup a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Update the environment variables:

A. Create a `.env` file.
B. Set the OpenAI API key. 
C. (Optional) Set the LLM model and mode.
```aiignore
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
LLM_MODE=mock
```

or you can run the following commands in the terminal:
```bash
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini
export LLM_MODE=mock
```


4. Run the app:
```bash
uvicorn app.main:app --reload
```

The docs (Swagger) can be found at http://127.0.0.1:8000/docs.

### Example

```bash
curl -s -X POST http://127.0.0.1:8000/analyze \  -H "Content-Type: application/json" \  -d '{"text":"OpenAI announced a new AI model today. Cloud providers reacted positively."}' | jq .

curl -s "http://127.0.0.1:8000/search?topic=AI" | jq .
```

---

## Endpoints

- `POST /analyze` → analyze one text or a batch
  - Body:
    - `text: string` **or** `texts: string[]`
  - Returns: `results: AnalysisPayload[]` (each contains `id, title, summary, sentiment, topics[3], keywords[3], confidence`)

- `GET /search?topic=xyz` → return stored analyses with matching topic/keyword

---

## Persistence

Uses SQLite (`analyzer.db`) via SQLAlchemy.
* The `analyses` table stores title, summary, sentiment, topics (JSON), keywords (JSON), raw input, and timestamp.

---

## Responses and Error Handling

- **Empty input** → 400 with a clear message.
- **LLM API failure** → 502 with error details; the server stays healthy.
- You can set `LLM_MODE=mock` to avoid external API calls entirely.

---

## Keywords (Noun) Extraction

The `app/keywords.py` module **does not call an LLM**. It implements a light tokenizer and counts probable nouns using:
- capitalization (non-sentence-start), 
- morphology suffixes (e.g., `-tion`, `-ment`, `-ity`), and
- hyphenated tokens.

---

## Bonus

- **Tests**: `pytest -q` (uses `LLM_MODE=mock`).
- **Docker**:
  ```bash
  docker build -t llm-extractor:latest .
  docker run -p 8000:8000 -e LLM_MODE=mock llm-extractor:latest
  ```
- **Confidence score**: a simple heuristic combining text length and keyword variety (`0.0–1.0`).

---

## Design Choices

I chose **FastAPI + SQLite** to ship a full vertical slice quickly with minimal dependencies and great developer ergonomics. The LLM integration is abstracted behind `app/llm.py`, which supports a **mock mode** for deterministic tests and local runs without network access. Keyword extraction is implemented locally in `app/keywords.py` with a small heuristic (no LLM calls) to satisfy the “implement yourself” requirement while avoiding heavyweight model downloads. Data storage is normalized into a single `analyses` table with JSON columns for topics/keywords so that search is simple but still flexible. Error handling ensures empty inputs and LLM failures return useful messages rather than crashing the process.

---

## Trade-offs

- The noun detector is intentionally simple; adding spaCy POS tagging would improve accuracy at the cost of setup time.
- Search uses `LIKE` over JSON strings; for larger datasets, you'd switch to Postgres with JSONB + GIN indexes or FTS.
- The prompt parser assumes a reasonably well-formed LLM reply; production code would use a stricter schema and retries.
- Batch processing is sequential for simplicity; a worker queue would scale better if needed.
