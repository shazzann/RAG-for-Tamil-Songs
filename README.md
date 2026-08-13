# RAG Tamil Songs 🎵

An end-to-end Retrieval-Augmented Generation (RAG) application that allows you to chat with the lyrics of Tamil songs! Ask questions like *"What songs talk about rivers?"* or *"Who composed the songs in Thiruchitrambalam?"* and the AI will retrieve the exact stanzas and metadata to answer you.

Built with a **FastAPI** backend, a **React/Vite** frontend with an ultra-premium glassmorphic UI, **Supabase** pgvector for storing embeddings, and powered by **Google Gemini**.

## 🚀 Features
- **Semantic Search**: Uses Gemini Embeddings to understand the meaning of your query, not just exact keywords.
- **Ultra-Premium UI**: Fully responsive React frontend featuring dynamic animated gradient mesh backgrounds, glassmorphism, and micro-animations.
- **Automated Web Scraper**: Included Python scripts to automatically scrape lyrics from Tamil song websites and chunk them by stanzas.
- **Docker & Kubernetes Ready**: Fully containerized and ready to deploy to your local Kubernetes cluster or the cloud.

---

## 🛠️ Tech Stack
- **Frontend**: React, TypeScript, Vite, Vanilla CSS
- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Database**: Supabase (PostgreSQL with `pgvector` extension)
- **AI Models**: Google Gemini (`gemini-2.5-flash` for chat, `text-embedding-3-small` for embeddings)
- **Deployment**: Docker, Kubernetes

---

## 💻 Local Development Setup (Native)

### 1. Database Setup
1. Create a free account on [Supabase](https://supabase.com).
2. Create a new project and go to the SQL Editor.
3. Run the SQL commands found in the Supabase documentation to enable `pgvector` and create your tables.

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create your environment variables file:
   - Copy `.env.example` to `.env`
   - Fill in your `DATABASE_URL` (use the IPv4 Connection Pooler string!) and `GEMINI_API_KEY`.
5. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
   *The API will be available at `http://localhost:8000`*

### 3. Frontend Setup
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```
   *The UI will be available at `http://localhost:5173`*

---

## 🐳 Running with Docker

You can easily run the entire application using Docker Compose without needing to set up Python or Node.js locally.

### 1. Configure Secrets
Copy `backend/.env.example` to `backend/.env` and fill in your API keys (make sure to use your Supabase IPv4 Pooler URL!).

### 2. Build and Run
From the root of the project, run:
```bash
docker build -t rag-backend:latest ./backend
docker build -t rag-frontend:latest ./frontend
docker-compose up
```
*The app will automatically launch and be available at `http://localhost`*

---

## ☸️ Running with Kubernetes

If you prefer to run the application in a containerized environment (like Docker Desktop), you can use the included Dockerfiles and Kubernetes manifests.

### 1. Build the Docker Images
From the root of the project:
```bash
docker build -t rag-backend:latest ./backend
docker build -t rag-frontend:latest ./frontend
```

### 2. Configure Kubernetes Secrets
1. Copy `k8s/secrets.example.yaml` to `k8s/secrets.yaml`.
2. Open `k8s/secrets.yaml` and paste your Supabase IPv4 Pooler string and your Gemini API key in plain text.
3. Apply the secrets to your cluster:
   ```bash
   kubectl apply -f k8s/secrets.yaml
   ```

### 3. Deploy to the Cluster
Apply the Deployments and Services:
```bash
kubectl apply -f k8s/
```
You can monitor the pods spinning up using `kubectl get pods`. Once they are `Running`, open `http://localhost` in your browser!

---

## 📚 Data Pipeline Scripts

To populate your database with new songs, use the scripts located in `backend/scripts/`:

1. **Scraper (`scrape_songs.py`)**: Scrapes lyrics from websites and saves them to a CSV.
2. **Chunker (`chunk_lyrics.py`)**: Splits the scraped songs into semantic stanzas.
3. **Embedder (`generate_embeddings.py`)**: Calls the Gemini Embedding API for each chunk and uploads the vector data to Supabase.
