# Tamil Song RAG Agent — Continuation Plan

## 1. Where the Project Stands

The project already has a strong **retrieval backend MVP**:

- FastAPI, PostgreSQL, Supabase, pgvector, and SQLAlchemy are implemented.
- Song metadata search, rule-based QA, lyric search, and semantic search exist.
- Gemini embeddings and MLflow evaluation are implemented.
- The main missing feature is the complete RAG experience:
  - Retrieve relevant context
  - Send it to an LLM
  - Generate a grounded natural-language answer
  - Return the answer with source information

The main retrieval problems identified so far are:

- Query expansion currently reduces performance.
- Tamil-script queries currently have `0% Hit@5`.
- One-line lyric chunks provide weak semantic context.
- Theme and semantic lyric searches need improvement.

---

## 2. Recommended Development Plan

### Phase 1 — Restore and Verify the Project

Complete these tasks before adding new features.

#### 1. Create a Development Branch

```bash
git checkout -b feature/rag-chat
```

#### 2. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

#### 3. Verify the Existing Endpoints

Open the FastAPI Swagger interface at:

```text
http://localhost:8000/docs
```

Test the following endpoints:

```text
GET /
GET /songs/
POST /qa/ask
GET /lyrics/semantic-search?q=love
```

#### 4. Run the Baseline Evaluation

Run the existing retrieval evaluation again and save the results.

#### 5. Verify the Database

Confirm that the database contains:

- 60 songs
- Generated lyric chunks
- Non-null 3072-dimensional embeddings

#### 6. Disable Query Expansion by Default

The existing evaluation shows that the baseline performs better:

| Version | Hit@5 | Precision@5 | MRR |
|---|---:|---:|---:|
| Baseline | 0.583 | 0.167 | 0.456 |
| Query expansion | 0.528 | 0.125 | 0.398 |

Do not focus on fixing query expansion before completing the main RAG pipeline.

---

### Phase 2 — Complete the RAG Chat Pipeline

This should be the next major implementation.

The target flow is:

```text
User question
    ↓
Query classification
    ↓
Metadata/SQL search or vector search
    ↓
Select relevant songs and lyric chunks
    ↓
Build grounded prompt
    ↓
Gemini generates an answer
    ↓
Return the answer with sources
```

#### Task 2.1 — Implement `llm_service.py`

Create an LLM service with an interface similar to:

```python
class LLMService:
    async def generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        ...
```

The system prompt should require the model to:

- Answer only using the retrieved context.
- Say when the answer cannot be found.
- Avoid inventing lyrics, singers, movies, composers, or lyricists.
- Mention the song title and movie when available.
- Answer in the language or script used by the user where practical.
- Avoid reproducing unnecessarily long lyric passages.

#### Task 2.2 — Create a Shared Retrieval Service

Do not keep all retrieval logic directly inside route files.

Create:

```text
backend/app/services/retrieval_service.py
```

A possible result model is:

```python
class RetrievedResult(BaseModel):
    song_id: int
    title: str
    movie: str | None
    chunk_text: str | None
    score: float | None
    source_type: str
```

The first version of the retrieval service should:

1. Detect exact or partial song-title matches.
2. Detect metadata questions about singers, composers, lyricists, or movies.
3. Use SQL filters for mood, year, person, and theme queries.
4. Fall back to semantic lyric search.
5. Return approximately five to eight relevant results.

#### Task 2.3 — Implement `POST /chat/`

Replace the hardcoded stub in `chat.py`.

Suggested request:

```json
{
  "message": "Which songs describe missing someone?",
  "top_k": 5
}
```

Suggested response:

```json
{
  "answer": "The retrieved songs that most closely describe...",
  "sources": [
    {
      "song_id": 12,
      "title": "Example Song",
      "movie": "Example Movie",
      "matched_text": "..."
    }
  ],
  "retrieval_type": "semantic",
  "latency_ms": 842
}
```

Returning sources is important because it:

- Demonstrates that the answer is grounded.
- Makes hallucinations easier to detect.
- Makes retrieval problems easier to debug.
- Gives the frontend useful source information.

---

### Phase 3 — Improve Retrieval Quality

Start this phase only after the `/chat/` endpoint works end to end.

#### 3.1 Replace One-Line Chunks with Stanza Chunks

The current chunks contain one lyric line. Create overlapping chunks containing approximately two to four lines.

Example:

```text
Chunk 1: lines 1–4
Chunk 2: lines 3–6
Chunk 3: lines 5–8
```

Then:

1. Delete or version the old chunks.
2. Generate the new stanza chunks.
3. Regenerate embeddings.
4. Run the same evaluation dataset.
5. Compare the experiment in MLflow.

This should improve semantic and theme retrieval because each embedding will contain more context.

#### 3.2 Implement Hybrid Retrieval

Use the correct retrieval method for each query type instead of applying vector search to everything.

| Query type | Preferred method |
|---|---|
| “Who composed Roja?” | SQL metadata lookup |
| “Songs by Anirudh after 2020” | SQL filters |
| “Songs about rain” | Theme filter plus semantic search |
| “Lyrics about missing someone” | Vector search |
| Exact lyric phrase | Keyword search plus vector search |

A simple first hybrid strategy is:

```text
Metadata results + keyword results + vector results
                         ↓
              Deduplicate by song/chunk
                         ↓
                 Combine and rank
```

A sophisticated reranker is not required yet.

#### 3.3 Add Tamil Transliteration

Tamil-script queries currently fail because the stored lyrics are in Tanglish.

Add a preprocessing layer:

```text
Tamil query
    ↓
Tamil-to-Latin transliteration
    ↓
Original query and transliterated query
    ↓
Embedding and retrieval
```

Store or process the two query forms separately instead of joining a large synonym list into one embedding query.

Evaluate Tamil-script and Tanglish queries separately.

#### 3.4 Replace Naive Query Expansion

Keep the concept dictionary for keyword and theme matching, but stop injecting every synonym into the embedding input.

Test these strategies separately:

- No expansion
- Transliteration only
- One canonical concept term
- LLM-generated query rewrite
- Multiple independently embedded query variants with score fusion

Record every strategy as a separate MLflow experiment.

---

### Phase 4 — Add Reliability and Tests

Before building a polished frontend, add a focused test suite.

Suggested structure:

```text
backend/tests/
├── test_health.py
├── test_songs.py
├── test_qa.py
├── test_semantic_search.py
├── test_chat.py
└── test_query_routing.py
```

Prioritize these test cases:

- A known title returns the correct song.
- Composer, singer, and lyricist questions return correct metadata.
- Unsupported questions do not produce fabricated answers.
- `/chat/` returns source records.
- Empty queries return HTTP 400 or 422.
- Database failures return a controlled error.
- Tamil queries pass through transliteration.
- Duplicate lyric chunks are not returned repeatedly.

Improve the health endpoint so that the API can report database availability without crashing:

```json
{
  "api": "healthy",
  "database": "unavailable"
}
```

The application should not terminate simply because Supabase is temporarily unreachable.

---

### Phase 5 — Clean the Project

Replace the 283-package `requirements.txt` with a minimal dependency list.

Likely dependencies include:

```text
fastapi
uvicorn
sqlalchemy
psycopg
pgvector
pydantic
pydantic-settings
python-dotenv
google-genai
pandas
mlflow
pytest
httpx
```

Use the exact packages and versions imported by the project.

Also add or improve:

```text
.env.example
README setup instructions
Database migration instructions
Evaluation instructions
```

Never commit the real `.env` file.

---

### Phase 6 — Build a Minimal Frontend

Do not start with a large dashboard.

Build a single Next.js page containing:

- Chat input
- Answer area
- Retrieved source cards
- Loading state
- Error state
- Example questions
- Optional language or script indicator

Each source card should display:

```text
Song title
Movie
Singer or composer
Matched lyric lines
Retrieval score or match reason
```

After the chat experience works, add metadata filters and browsing features.

---

### Phase 7 — Deployment

Deploy only after the chat endpoint and basic tests are stable.

Suggested architecture:

```text
Next.js frontend → Vercel
FastAPI backend → Railway or Render
PostgreSQL and pgvector → Supabase
MLflow → Local initially or a separate hosted service
```

Also configure:

- CORS
- Environment-specific API URLs
- Production secrets
- Structured logging
- Basic monitoring

---

## 3. Two-Week Execution Plan

### Days 1–2 — Restore and Stabilize

- Run the full project.
- Verify the database, chunks, and embeddings.
- Run the baseline evaluation.
- Disable query expansion by default.
- Clean `requirements.txt`.
- Add `.env.example`.

### Days 3–5 — Finish the RAG MVP

- Implement `llm_service.py`.
- Create `retrieval_service.py`.
- Implement context construction.
- Complete `POST /chat/`.
- Return source information.
- Manually test approximately 15 representative questions.

### Days 6–8 — Improve Retrieval

- Implement stanza-based chunking.
- Regenerate embeddings.
- Add hybrid retrieval.
- Re-run MLflow experiments.
- Compare the results against the original baseline.

### Days 9–10 — Add Tamil Support

- Add Tamil-script detection.
- Add transliteration.
- Evaluate Tamil and Tanglish queries separately.
- Remove or revise expansion rules that reduce performance.

### Days 11–12 — Tests and Resilience

- Add API and retrieval tests.
- Improve database error handling.
- Add request validation.
- Add structured logging.
- Add latency measurements.

### Days 13–14 — Minimal Frontend

- Create the Next.js project.
- Build the chat screen.
- Display retrieved sources.
- Connect the frontend to the FastAPI backend.

---

## 4. Suggested Success Criteria

Use these as the next project targets:

- `POST /chat/` generates grounded answers with source records.
- No `NotImplementedError` or hardcoded chat response remains.
- Overall `Hit@5` reaches at least `0.70`.
- Tamil-query `Hit@5` becomes greater than zero and continues improving.
- Query expansion is enabled only when an experiment shows improvement.
- Every generated answer includes a source or clearly states that information is insufficient.
- Core API and chat tests pass.
- The frontend can complete one end-to-end chat request.

---

## 5. Immediate Next Task

The next development sequence should be:

```text
Implement llm_service.py
        ↓
Create retrieval_service.py
        ↓
Complete POST /chat/
```

Do not begin with the scraper, reranker, large dataset, or polished frontend.

A working, grounded chat pipeline will turn the components already built into a complete RAG application. After that, every retrieval improvement can be measured using both the evaluation scripts and the generated answers.
