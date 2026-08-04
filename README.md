# DevInsight

An AI-powered assistant that ingests a public GitHub repository, indexes its code, and helps a
developer understand and contribute to it: RAG-based Q&A with citations, auto-generated
architecture diagrams, beginner-friendly contribution recommendations, AI-drafted pull requests,
and unit test generation.

**Backend:** Django + DRF, JWT auth, Postgres (pgvector) in production / SQLite + ChromaDB locally.
**Frontend:** React (Vite) + Tailwind CSS.
**Chat completions:** Groq (OpenAI-compatible). **Embeddings:** free local model (`fastembed`) by
default, or OpenAI's embeddings API.

![Landing page](docs/screenshots/landing.png)

## Features

- **Ingestion**: paste a public GitHub repo URL → downloads it, chunks the source files, embeds
  them in bounded batches, and stores the vectors — locally in ChromaDB during development, or in
  Postgres via the `pgvector` extension in production so the index survives redeploys. Live status
  (`pending → fetching → chunking → embedding → completed`) is shown in the UI.
- **Chat (RAG)**: ask natural-language questions about the repo; answers are grounded in retrieved
  code chunks and cite the exact file/line ranges. Each repo keeps its own chat sessions —
  switchable, deletable, and rendered as real markdown so copy/paste preserves formatting.
- **Architecture diagrams**: parses import/require statements to build a module dependency graph,
  rendered as Mermaid diagrams (a high-level overview plus per-module class diagrams), with an
  AI-written summary.
- **Contribution recommendations**: pulls real open issues from GitHub (preferring `good first
  issue`/`help wanted` labels), grounds each in relevant code, and summarizes it for a newcomer.
- **PR draft assistant**: given an issue or a task description, retrieves the most relevant file,
  has the AI propose a change, and produces a real unified diff for you to review — nothing is
  pushed to GitHub automatically.
- **Test case generator**: pick a file (or describe a task) and get a generated test suite — happy
  path, edge cases, and mocked dependencies — with an explanation of what's covered.
- **Staleness detection**: on-demand check for whether a repo's default branch has moved past the
  commit that was actually indexed, with a one-click re-index.
- **Auth**: email/password signup and login (JWT), plus OTP-based password reset — a 6-digit code
  emailed to you, verified on-site, no email links.

| Chat with citations | Architecture diagram |
|---|---|
| ![Chat](docs/screenshots/chat.png) | ![Architecture](docs/screenshots/architecture.png) |

| Contribution recommendations | PR draft assistant |
|---|---|
| ![Recommendations](docs/screenshots/recommendations.png) | ![PR Assistant](docs/screenshots/pr-assistant.png) |

| Test case generator | Repository overview |
|---|---|
| ![Test Generator](docs/screenshots/test-generator.png) | ![Overview](docs/screenshots/overview.png) |

## Project layout

```
backend/    Django + DRF API — accounts (auth/OTP), repos (ingestion), chat (RAG), contrib (architecture/recommendations/PR drafts/tests)
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

- **Database** — defaults to a local SQLite file, no setup needed. In production, set
  `DATABASE_URL` to a real Postgres connection string (e.g. from [Neon](https://neon.tech)'s free
  tier) so data survives redeploys — a Web Service's local disk doesn't.
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
- **Embeddings** — defaults to `EMBEDDING_PROVIDER=local`, which runs a free ONNX model
  (`fastembed`, no torch dependency) on CPU with no API key or billing at all. (Groq has no
  embeddings endpoint, so embeddings stay local even when chat uses Groq.) Set
  `EMBEDDING_PROVIDER=openai` instead to use OpenAI's embeddings API, which requires
  `OPENAI_API_KEY` — vectors are stored as fixed-width columns in Postgres, so switching providers
  in production requires re-indexing existing repos.
- **Password reset email** — defaults to printing the OTP email to the console, zero setup for
  local dev. For real delivery, switch to the SMTP backend and fill in the `EMAIL_HOST_*` vars
  (Gmail SMTP, SendGrid, Mailgun, etc.) — see the inline comments in `.env.example`.
- `GITHUB_TOKEN` is optional and only needed if you hit GitHub's unauthenticated API rate limit
  (60 requests/hour; a token raises it to 5,000/hour).

```bash
python manage.py migrate
python manage.py runserver
```

The API is served at `http://localhost:8000/api/`. The first request that needs embeddings will
download the local model (~90MB, one-time, cached under your home directory).

### Running the backend with Docker

An alternative to the venv setup above — a multi-stage `backend/Dockerfile` builds a slim,
non-root runtime image:

```bash
docker build -t devinsight-backend backend/
docker run --rm -p 10000:10000 --env-file backend/.env devinsight-backend
```

The API is then served at `http://localhost:10000/api/`. This is unrelated to how the app is
actually deployed (see [Deployment](#deployment)) — it's a self-contained way to build and run
the backend without a local Python environment, e.g. for testing on another machine or platform.

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
   ~40-line chunks. `ingest.py` orchestrates the pipeline in a background thread: chunks and embeds
   in bounded batches (flushed to the vector store as it goes, rather than holding an entire repo's
   text in memory at once), and stores vectors via `vectorstore/client.py`, which dispatches to a
   ChromaDB-backed store locally (SQLite dev) or a Postgres/`pgvector`-backed store in production
   (detected automatically from the database connection). Progress is tracked via
   `Repository.status`, polled by the frontend every few seconds. If the server restarts
   mid-ingestion, `repos/apps.py` resets any stuck job to `failed` on startup.
2. **Chat/RAG** (`chat/services/rag.py`): embeds the user's question, retrieves the top-k similar
   chunks for the repo, builds a grounded prompt (with recent chat history), and calls the chat
   completion API. Returns the answer plus citations (`file_path`, `start_line`, `end_line`). Each
   conversation is a `ChatSession`, so a repo can have multiple, independently switchable threads.
3. **Architecture** (`contrib/services/architecture.py`, `imports_parser.py`): reads each file's
   first indexed chunk (where imports live) straight from the vector store — no repo re-download
   needed — parses imports per language, resolves internal-only edges, aggregates to a module-level
   graph, and renders Mermaid. The AI summary is best-effort and degrades gracefully if the chat API
   fails.
4. **Recommendations** (`contrib/services/recommendations.py`, `github_issues.py`): fetches real
   open GitHub issues, prefers beginner-friendly labels with a fallback to recent issues, and asks
   the AI for a grounded summary per issue (also best-effort/gracefully degrading).
5. **PR drafts** (`contrib/services/pr_draft.py`): RAG-retrieves the most relevant file for a task,
   re-downloads the repo to read that file's pristine original content, has the AI propose a full
   replacement via a structured prompt, and computes a real unified diff with `difflib`.
6. **Test generation** (`contrib/services/test_generator.py`): RAG-picks a target file (or uses an
   explicit one), fetches its raw source, and asks the AI for a structured response — explanation,
   framework, file name, and test code — covering the happy path, edge cases, and mocked
   dependencies.
7. **Password reset** (`accounts/`): a `PasswordResetOTP` model generates a 6-digit code with a
   10-minute expiry. The frontend flow is three explicit steps — request a code, verify it (without
   consuming it, so a wrong entry doesn't burn the real code), then set a new password — with an
   HTML-formatted email (`accounts/emails.py`).

## Deployment

This app is deployed as three separate free-tier services:

- **Backend**: [Render](https://render.com) Web Service (`gunicorn config.wsgi`), Root Directory
  `backend`, Python pinned via `runtime.txt`.
- **Frontend**: [Vercel](https://vercel.com), with `frontend/vercel.json` providing the SPA
  rewrite rule client-side routes need on reload.
- **Database**: [Neon](https://neon.tech) serverless Postgres (with the `pgvector` extension for
  the embedding index), so data survives every backend redeploy.

See `backend/.env.example` for the full list of environment variables each service needs.

## Notes / production considerations

- Ingestion runs on a plain Python thread for simplicity — swap in Celery + Redis/RabbitMQ if you
  need retries, multi-worker scaling, or to survive server restarts mid-ingestion.
- Local embeddings (`fastembed`) are memory-light compared to a full `torch`-based model, but a
  512MB-RAM host still has very little headroom once the model is loaded — large repos may need a
  bigger instance, or `EMBEDDING_PROVIDER=openai`, to index reliably.
- Rotate any credentials (API keys, `SECRET_KEY`, email app passwords) that have ever been shared
  or committed anywhere outside your own `.env`/host dashboard.
