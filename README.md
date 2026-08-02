# AI Codebase Understanding Assistant

An AI-powered assistant that ingests a public GitHub repository, indexes its code with embeddings,
and helps a developer understand it: RAG-based Q&A, an auto-generated architecture diagram,
beginner-friendly contribution recommendations, and AI-drafted pull requests. Backend: Django + DRF
+ ChromaDB. Frontend: React (Vite) + Tailwind CSS.

## Features

- **Ingestion**: paste a public GitHub repo URL → downloads it, chunks the source files, embeds
  them, and stores them in a local ChromaDB collection, with live status shown in the UI.
- **Chat (RAG)**: ask natural-language questions about the repo; answers are grounded in retrieved
  code chunks and cite the source file/line ranges.
- **Architecture diagrams**: parses import/require statements to build a module dependency graph,
  rendered as a Mermaid diagram, plus an AI-written architecture summary.
- **Contribution recommendations**: pulls real open issues from GitHub (preferring `good first
  issue`/`help wanted` labels), grounds each in relevant code, and summarizes it for a newcomer.
- **PR draft assistant**: given an issue or a task description, retrieves the most relevant file,
  has the AI propose a change, and produces a real unified diff for you to review — nothing is
  pushed to GitHub automatically.

## Project layout

```
backend/    Django + DRF API — repos (ingestion), chat (RAG), contrib (architecture/recommendations/PR drafts)
frontend/   React + Tailwind SPA
```

## Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
copy .env.example .env       # Windows: copy, macOS/Linux: cp
```

Edit `backend/.env`:

- **Chat completions** — any OpenAI-compatible API works. Two easy options are documented inline in
  `.env.example`:
  - **Groq** (free tier, fast): get a key at https://console.groq.com/keys, set `LLM_API_KEY`,
    `LLM_BASE_URL=https://api.groq.com/openai/v1`, `LLM_CHAT_MODEL=llama-3.3-70b-versatile`.
  - **OpenAI**: get a key at https://platform.openai.com/api-keys, set `LLM_API_KEY`, leave
    `LLM_BASE_URL` empty, `LLM_CHAT_MODEL=gpt-4o-mini`.

  Prompt sizes (`RAG_TOP_K`, chat history length, PR-draft file size cap) default to conservative
  values tuned to fit under Groq's free-tier rate limit (12,000 tokens/minute, shared across the
  whole app) — see `RAG_TOP_K` and `MAX_PR_FILE_SIZE_BYTES` in `config/settings.py`. If you're on
  a paid tier or a provider with a higher limit, raise them via `.env` for better answer quality.
- **Embeddings** — defaults to `EMBEDDING_PROVIDER=local`, which runs a free `sentence-transformers`
  model on CPU with no API key or billing at all. (Groq has no embeddings endpoint, so embeddings
  stay local even when chat uses Groq.) Set `EMBEDDING_PROVIDER=openai` instead to use OpenAI's
  embeddings API, which requires `OPENAI_API_KEY`.
- `GITHUB_TOKEN` is optional and only needed if you hit GitHub's unauthenticated API rate limit.

```bash
python manage.py migrate
python manage.py runserver
```

The API is served at `http://localhost:8000/api/`. The first request that needs embeddings will
download the local model (~90MB, one-time, cached under your home directory).

## Frontend setup

```bash
cd frontend
npm install
copy .env.example .env       # Windows: copy, macOS/Linux: cp
npm run dev
```

The app is served at `http://localhost:5173`. It talks to the backend at the URL configured in
`frontend/.env` (`VITE_API_BASE_URL`, defaults to `http://localhost:8000/api`).

## How it works

1. **Ingestion** (`repos/services/`): `fetch.py` resolves the GitHub URL and downloads a tarball via
   GitHub's public codeload endpoint (no `git` binary or auth needed for public repos). `chunker.py`
   walks the tree, skips binary/vendor/lockfile noise, and splits text files into overlapping
   ~40-line chunks. `ingest.py` orchestrates the pipeline in a background thread, embeds each chunk
   batch, and stores vectors in a per-repo ChromaDB collection (`vectorstore/client.py`). Progress is
   tracked via `Repository.status` (`pending → fetching → chunking → embedding → completed/failed`),
   polled by the frontend every 2s. If the server restarts mid-ingestion, `repos/apps.py` resets any
   stuck job to `failed` on startup (the background thread doesn't survive a restart).
2. **Chat/RAG** (`chat/services/rag.py`): embeds the user's question, retrieves the top-k similar
   chunks from the repo's Chroma collection, builds a grounded prompt (with recent chat history),
   and calls the chat completion API. Returns the answer plus citations (`file_path`, `start_line`,
   `end_line`).
3. **Architecture** (`contrib/services/architecture.py`, `imports_parser.py`): reads each file's
   first indexed chunk (where imports live) straight from Chroma — no repo re-download needed —
   parses imports per language, resolves internal-only edges, aggregates to a module-level graph,
   and renders Mermaid. The AI summary is best-effort and degrades gracefully if the chat API fails.
4. **Recommendations** (`contrib/services/recommendations.py`, `github_issues.py`): fetches real
   open GitHub issues, prefers beginner-friendly labels with a fallback to recent issues, and asks
   the AI for a grounded summary per issue (also best-effort/gracefully degrading).
5. **PR drafts** (`contrib/services/pr_draft.py`): RAG-retrieves the most relevant file for a task,
   re-downloads the repo to read that file's pristine original content, has the AI propose a full
   replacement via a structured prompt, and computes a real unified diff with `difflib`.

## Notes / production considerations

- Ingestion runs on a plain Python thread for simplicity — swap in Celery + Redis/RabbitMQ if you
  need retries, multi-worker scaling, or to survive server restarts mid-ingestion.
- SQLite is used for simplicity; swap `DATABASES` in `backend/config/settings.py` for Postgres in
  production.
- ChromaDB persists to `backend/chroma_data/` (configurable via `CHROMA_PERSIST_DIR`).
