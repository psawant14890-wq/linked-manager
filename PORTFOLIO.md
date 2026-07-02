# LinkedIQ -- Portfolio Notes

## Resume bullets

### GenAI Fullstack track
- Built LinkedIQ, a fullstack GenAI application (Next.js/FastAPI) where AI is load-bearing across 4 features: GPT-4o message classification with Pydantic-enforced structured output, RAG-lite post generation using pgvector similarity retrieval over a user's own writing history, and two SSE-streamed generation pipelines (reply drafts, weekly reports).
- Designed a retrieval pipeline using OpenAI embeddings + pgvector cosine similarity to ground LLM post generation in a user's authentic writing style, rather than generic prompt-only generation.
- Implemented a validate-and-retry contract for every LLM call: Pydantic v2 schemas define the exact shape the model must return, with one automatic retry on validation failure before falling back to a clearly-flagged manual-review state -- no silent failures, no unvalidated model output reaching the database.

### Python Developer track
- Built an async FastAPI backend (SQLAlchemy 2.0 async ORM, Alembic migrations, Pydantic v2) with a consistent `{success, data, error}` response envelope across every endpoint.
- Wrote a defensive CSV/zip parser for real-world LinkedIn data exports that tolerates format drift (variant column names, preamble rows, malformed rows) and reports exactly what was/wasn't imported per file, covered by unit tests with no external dependencies.
- Implemented JWT-based service-to-service auth (FastAPI issuing/verifying its own tokens, consumed by a separate Next.js frontend via NextAuth), keeping the API consumable by any client, not just the bundled frontend.

### SDE / general fullstack track
- Shipped a complete fullstack product end-to-end: schema design, async API, AI integration, streaming UI, Dockerized deployment to Railway -- solo, with a deliberate scope boundary (ToS-compliant data import vs. live API access) documented and defended rather than glossed over.
- Designed the data model and migration (Postgres + pgvector) for a system with both relational data (messages, posts, connections) and vector similarity search in the same database, avoiding a separate vector store.

## What this project can and cannot honestly claim

**Can claim:**
- A fully working, AI-central product where removing the AI breaks the core features (classification, generation, and reporting are not bolted-on -- they're the product).
- A genuinely ToS-compliant approach to a category (LinkedIn tooling) where almost every public example you'll find uses scraping or unofficial APIs. This is a real differentiator in an interview, not a workaround to apologize for.
- Real engineering practices: typed end-to-end, structured-output validation with retry logic, async throughout, tested parsing logic, Dockerized, deployed.
- A working RAG pipeline (small-scale, but real: embeddings, vector storage, similarity retrieval, few-shot grounding) -- not just "I called the OpenAI API."

**Cannot claim:**
- Real-time or live data. The app only knows what was in the user's last export; there's no webhook, no polling, no "new message just arrived" experience. This is explicitly framed as on-demand (the weekly report is a button, not a cron job) rather than disguised as live.
- Automated sending or posting. Nothing in this project posts or messages on the user's behalf, and that's a design decision, not a missing feature -- don't let it get read as "couldn't figure out the API," because the framing is "chose not to violate ToS."
- Classification accuracy guarantees. The GPT-4o classifier is good but not perfect; the `needs_review` fallback state exists because misclassification is expected, not an edge case being ignored.

## Likely interview questions

**"Why didn't you use the LinkedIn API directly?"**
Because LinkedIn's official API doesn't grant individual developers access to read personal messages or post/send on a user's behalf -- that access is restricted to approved partners. The alternative most portfolio projects in this space take is scraping or browser automation, which violates LinkedIn's Terms of Service and would put any real user's account at risk. I designed around the actual constraint: LinkedIn already provides every user a built-in, ToS-compliant data export. I built the product as the analysis and AI layer on top of that export instead. It's a real architectural decision with a real tradeoff (no live data), not a workaround -- and I can speak to why I'd make the same call again.

**"How would you make this real-time / live?"**
The honest answer: a personal LinkedIn account fundamentally can't have a live integration without violating ToS, so "real-time" isn't reachable as a personal project. If this were a B2B product, the path would be LinkedIn's official Partner Program / Marketing Developer Platform, which does grant broader API access under a formal partnership agreement -- that's a sales/business-development path, not an engineering one.

**"How do you handle bad LLM output?"**
Every structured LLM call is wrapped against a strict Pydantic schema with `extra="forbid"`. On a validation failure, I retry once with the validation error appended to the prompt as a correction instruction. If it fails twice, the message is flagged `needs_review` rather than silently dropped or stored with garbage data -- so a model hiccup degrades gracefully into "ask a human" instead of corrupting state.

**"Why pgvector instead of a dedicated vector DB (Pinecone, Weaviate, etc.)?"**
Scale. This is per-user similarity search over a few hundred posts at most, not millions of vectors across tenants -- a dedicated vector DB would be operational overhead with no real benefit here. pgvector keeps relational data (the post's text, engagement metrics, timestamps) and its embedding in the same row, in the same database I'm already running, with one fewer service to deploy and pay for. I'd reach for a dedicated vector store if this became a multi-tenant product indexing millions of documents with strict latency SLAs.

**"What was the hardest part?"**
Realistically: making the LinkedIn CSV parser tolerant of real-world export quirks -- LinkedIn's export format isn't a stable, documented schema, so the parser has to handle preamble rows, column-name variants, and partial failures without crashing the whole import. That's reflected in the `parse_upload` design (one result per file, never one failure for the whole batch) and is covered by unit tests using synthetic CSVs that mimic those quirks.

**"What would you build next if you had another week?"**
A background job queue (e.g., Celery/RQ or a simple async task runner) so classification happens asynchronously during import instead of needing a follow-up call per message, plus batch re-embedding for posts that failed to embed during import (currently best-effort and silently skipped on provider errors).

**"Why does this use both xAI's Grok and a local embedding model instead of one provider for everything?"**
Two independent decisions, not one compromise. For chat/generation, the app talks to a provider through the OpenAI SDK with a configurable `base_url` -- it currently points at xAI's Grok API, but swapping back to OpenAI is a two-line env change, no code changes, because xAI's API is intentionally OpenAI-SDK compatible. For embeddings, the app never calls an external embeddings API at all -- it runs `fastembed` (ONNX runtime) locally in the same container. That's not a Grok-specific workaround; it's true independent of chat provider, since xAI doesn't currently expose a public embeddings endpoint and running embeddings locally removes an external dependency and its per-call cost entirely. The practical result: the whole app runs at zero marginal API cost beyond whatever free tier the chat provider offers, and the two concerns (generation vs. retrieval) are decoupled enough that either one can be swapped without touching the other.
