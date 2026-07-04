# 🎶 Tamil Song RAG Agent

A RAG (Retrieval-Augmented Generation) powered application for searching and querying Tamil songs by title, lyrics meaning, singer, lyricist, composer, and more.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js / React |
| Backend | FastAPI |
| Database | PostgreSQL + pgvector |
| Scraping | Python / BeautifulSoup |
| LLM | Gemini or OpenAI |
| Embeddings | OpenAI / Gemini / multilingual model |
| Deployment | Vercel + Railway or Supabase |

## MVP Features

1. Search song by title
2. Ask who wrote a song
3. Ask songs by singer / lyricist / composer / year
4. Search lyric lines by meaning (semantic search)
5. Ask analytical questions (sad songs, love songs, songs about eyes, etc.)

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── database.py      # PostgreSQL + pgvector setup
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Embedding & LLM services
│   │   └── utils/           # Helper utilities
│   ├── scripts/
│   │   ├── seed_songs.py           # Seed DB from CSV
│   │   ├── scrape_songs.py         # Web scraper
│   │   └── generate_embeddings.py  # Generate vector embeddings
│   ├── data/
│   │   └── sample_songs.csv
│   ├── requirements.txt
│   └── .env
├── frontend/                # Next.js app (coming soon)
├── README.md
└── .gitignore
```

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## License

MIT
