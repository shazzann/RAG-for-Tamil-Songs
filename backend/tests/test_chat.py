"""
Tests for the RAG Chat pipeline (POST /chat/) and retrieval routing.
Uses an in-memory SQLite database to verify routing offline and reliably.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.models import Song

# In-memory SQLite engine for unit testing offline with StaticPool so memory DB persists across sessions
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestChatEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        db = TestingSessionLocal()
        # Seed test songs
        song1 = Song(
            id=1,
            title="Roja Janapathi",
            movie="Roja",
            year=1992,
            singers="S. P. Balasubrahmanyam",
            lyricist="Vairamuthu",
            composer="A. R. Rahman",
            mood="Romantic",
            themes="love;nature",
            lyrics="Chinna chinna aasai..."
        )
        song2 = Song(
            id=2,
            title="Why This Kolaveri Di",
            movie="3",
            year=2011,
            singers="Dhanush",
            lyricist="Dhanush",
            composer="Anirudh Ravichander",
            mood="Sad",
            themes="love;soup",
            lyrics="Yo boys I am singing song..."
        )
        db.add_all([song1, song2])
        db.commit()
        db.close()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=test_engine)

    def test_empty_question(self):
        """Empty query should return HTTP 400 or 422 validation error."""
        response = client.post("/chat/", json={"question": ""})
        self.assertIn(response.status_code, [400, 422])

    def test_factual_metadata_query(self):
        """Factual query about a known song should route to metadata retrieval."""
        response = client.post("/chat/", json={"question": "Who composed Roja Janapathi?"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)
        self.assertIn("sources", data)
        self.assertEqual(data["retrieval_type"], "metadata")
        self.assertGreaterEqual(data["latency_ms"], 0.0)
        self.assertTrue(any("Roja Janapathi" in s["title"] for s in data["sources"]))

    def test_analytical_filter_query(self):
        """Analytical filter query (e.g. sad songs) should route via SQL metadata."""
        response = client.post("/chat/", json={"question": "Which songs are sad?"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["retrieval_type"], "metadata")
        self.assertTrue(any("Why This Kolaveri Di" in s["title"] for s in data["sources"]))

    def test_conversational_greeting(self):
        """Greeting should return a polite response without crashing."""
        response = client.post("/chat/", json={"question": "Hello! What can you do?"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)

    @patch("app.services.llm_service.client")
    def test_llm_error_graceful_fallback(self, mock_client):
        """If Gemini LLM raises an exception, endpoint should degrade gracefully."""
        mock_client.models.generate_content.side_effect = Exception("Simulated API timeout")
        response = client.post("/chat/", json={"question": "Who composed Roja Janapathi?"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("issue", data["answer"].lower() or "error" in data["answer"].lower())
        self.assertIsInstance(data["sources"], list)
        self.assertTrue(len(data["sources"]) > 0)


if __name__ == "__main__":
    unittest.main()
