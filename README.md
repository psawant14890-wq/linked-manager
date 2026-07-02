# LinkedIQ

AI-powered LinkedIn management tool, built entirely on **LinkedIn's official "Download your data" export** -- no scraping, no browser automation, no unofficial API calls, no automated sending. The user exports their own data from LinkedIn, uploads it here, and the app does inbox triage, style-matched post drafting, reply drafting, and weekly activity reporting on top of it. Every AI output is a draft the user reviews and sends manually.

## Why this architecture

LinkedIn's official API does not grant individual developers access to personal messages or posting on behalf of a user, and scraping/automation violates LinkedIn's Terms of Service. Rather than work around that, this project treats it as the actual constraint to design for: LinkedIn already ships a built-in, ToS-compliant data export to every user. This app is the analysis and drafting layer on top of that export.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript (strict), Tailwind CSS, React Query, SSE streaming client |
| Backend | FastAPI (async), SQLAlchemy 2.0 (async ORM), Pydantic v2, Alembic |
| AI | OpenAI GPT-4o (classification, generation, reports), text-embedding-3-small, pgvector for RAG-lite style retrieval |
| Database | PostgreSQL 16 + pgvector |
| Auth | NextAuth.js (credentials) + FastAPI-issued JWTs |
| Deploy | Docker + docker-compose locally; Supabase (DB) + Render (backend) + Vercel (frontend) in production -- a genuinely $0/mo stack |

## Project structure

```
linkediq/
├── backend/                 FastAPI service
│   ├── app/
│   │   ├── api/             route handlers (one file per feature)
│   │   ├── core/            llm client, SSE helpers, security/JWT
│   │   ├── models/          SQLAlchemy ORM models
│   │   ├── schemas/         Pydantic request/response + LLM-output schemas
│   │   └── services/        business logic: parser, classifier, embeddings,
│   │                        post generator, reply generator, report generator
│   ├── alembic/              migrations (0001 creates the full schema + pgvector)
│   └── tests/                 unit tests for parser + priority scoring
├── frontend/                 Next.js app
│   ├── app/                   pages: dashboard, inbox, generate, analytics, reports, import, login/register
│   ├── components/            ui primitives + feature components
│   ├── hooks/                  React Query hooks
│   └── lib/                    api client, auth config, shared types
└── docker-compose.yml         backend + frontend + postgres/pgvector together
```

## Local setup

### 1. Prerequisites
- Docker + Docker Compose (easiest path), **or** Python 3.12 + Node 20 + a local Postgres 16 with the pgvector extension available
- A chat API key -- **this project can run at zero cost**, see below

### 2. Zero-cost setup (default, recommended)

Chat/generation (classification, replies, posts, reports, job extraction) can run on **xAI's Grok API** instead of OpenAI -- xAI's API is OpenAI-SDK compatible, so this needs zero code changes, only a config swap. Get a Grok key at [console.x.ai](https://console.x.ai).

Embeddings (used for style-matching post generation and connection semantic search) run **100% locally** via [`fastembed`](https://github.com/qdrant/fastembed) (ONNX runtime) -- no API key, no external call, no cost, regardless of which chat provider you use. The model downloads once (~130MB) during the Docker build and then runs entirely offline.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

`backend/.env.example` is already configured for this zero-cost setup by default:
```env
OPENAI_API_KEY=xai-replace-with-your-grok-key
OPENAI_BASE_URL=https://api.x.ai/v1
OPENAI_CHAT_MODEL=grok-4.3
```
Edit `backend/.env`: paste your real Grok key in place of `xai-replace-with-your-grok-key`, and set `JWT_SECRET` to a random string. Edit `frontend/.env.local` and set `NEXTAUTH_SECRET` to a random string (`openssl rand -base64 32` works well for both secrets).

**To use OpenAI instead of Grok**, edit `backend/.env` and swap in:
```env
OPENAI_API_KEY=sk-replace-with-your-openai-key
OPENAI_BASE_URL=
OPENAI_CHAT_MODEL=gpt-4o
```
Embeddings stay local either way -- that part of the config never changes.

### 3a. Run with Docker (recommended)
```bash
docker compose up --build
```
This starts Postgres (with pgvector) on `5432`, the backend on `8000`, and the frontend on `3000`. The backend container runs `alembic upgrade head` automatically on startup, so the schema is created for you.

### 3b. Run without Docker
```bash
# Postgres: make sure a local Postgres 16 instance is running and the
# `vector` extension is installable (the pgvector/pgvector Docker image
# handles this for you; a bare local Postgres install needs the pgvector
# extension built/installed separately).

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### 4. Open the app
Visit `http://localhost:3000`, register an account, then go to **Import data** and upload your LinkedIn export.

### 5. Run backend tests
```bash
cd backend
pytest
```

## Where to get a real LinkedIn data export to test with

LinkedIn → click your profile photo → **Settings & Privacy** → **Data privacy** → **Get a copy of your data**. Choose "Want something in particular? Select the data files you're most interested in" or request the full archive, and make sure **Messages**, **Connections**, and **the article, post, and comment data (Shares)** are included. LinkedIn emails you a download link, usually within a few minutes to about 24 hours, as a `.zip`. Upload that zip directly on the Import page -- the parser looks for `Messages.csv`, `Shares.csv`, and `Connections.csv` inside it. If your account also has post-level analytics, LinkedIn lets you export those separately from your post analytics view; that CSV can be uploaded too to populate view/like/comment counts on the Analytics page.

## What "draft only" means in practice

Every AI-generated reply and post lives in `generated_drafts`, is streamed into an editable text box, and is labeled "Draft -- review before sending/posting" in the UI. There is no code path anywhere in this project that posts to LinkedIn or sends a message on the user's behalf -- copying and sending is a manual, human step every time.
