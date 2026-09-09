# LimkoBot — System Specifications

Hybrid RAG WhatsApp Chatbot for Limkokwing University
Phase 1 · Design Finalization

## 1. Overview

LimkoBot answers prospective and current students' questions about admissions, programmes, fees, campus life, and university policies via WhatsApp using a hybrid Retrieval-Augmented Generation (RAG) pipeline backed by an admin dashboard for knowledge-base management and analytics.

## 2. Tech Stack

| Layer      | Technology                                    |
|------------|-----------------------------------------------|
| Backend    | FastAPI (Python 3.11)                         |
| Database   | PostgreSQL via Supabase (+ pgvector for embeddings) |
| WhatsApp   | Twilio WhatsApp API                           |
| RAG        | OpenAI embeddings + chat completions, LangChain |
| Auth       | JWT (python-jose), OTP verification via email |
| Frontend   | Admin dashboard (Next.js-style, port 3000)    |
| CI/CD      | GitHub Actions (lint/test), Render deploy     |

## 3. Database Schema

All primary keys are UUIDs (`gen_random_uuid()`), timestamps are `TIMESTAMPTZ DEFAULT now()`. Embeddings are stored as `vector(1536)` using the pgvector extension.

### 3.1 users

Identifies students and admins. Auth is phone + OTP based (no passwords).

| Column          | Type                | Notes                                              |
|-----------------|---------------------|----------------------------------------------------|
| id              | UUID PK             | `default: gen_random_uuid()`                      |
| phone           | TEXT UNIQUE NOT NULL | WhatsApp number (E.164, e.g. `+260...`)          |
| full_name       | TEXT                |                                                    |
| student_id      | TEXT UNIQUE         | Student number; NULL for admins                    |
| email           | TEXT                | Used for OTP delivery                              |
| role            | TEXT NOT NULL       | `student` \| `admin`, default `student`            |
| is_verified     | BOOLEAN             | default `false`                                    |
| otp_code        | TEXT                | 6-digit code                                       |
| otp_expires_at  | TIMESTAMPTZ         |                                                    |
| created_at      | TIMESTAMPTZ         | default `now()`                                    |
| updated_at      | TIMESTAMPTZ         | default `now()`                                    |

### 3.2 conversations

A chat session between a user and the bot.

| Column           | Type                | Notes                                        |
|------------------|---------------------|----------------------------------------------|
| id               | UUID PK             |                                              |
| user_id          | UUID FK → users.id  | `ON DELETE CASCADE`                          |
| channel          | TEXT NOT NULL       | default `whatsapp`                           |
| status           | TEXT NOT NULL       | `active` \| `closed`, default `active`       |
| metadata         | JSONB               | session metadata                             |
| started_at       | TIMESTAMPTZ         | default `now()`                              |
| last_message_at  | TIMESTAMPTZ         | updated on each message                      |

### 3.3 messages

Individual user/bot messages within a conversation.

| Column          | Type                    | Notes                                      |
|-----------------|-------------------------|--------------------------------------------|
| id              | BIGSERIAL PK            |                                            |
| conversation_id | UUID FK → conversations.id | `ON DELETE CASCADE`                     |
| sender          | TEXT NOT NULL           | `user` \| `bot` \| `system`                |
| body            | TEXT NOT NULL           | message text                               |
| message_type    | TEXT NOT NULL           | `text`, default                            |
| intent          | TEXT                    | detected intent (null if unknown)          |
| confidence      | FLOAT                   | model confidence 0–1                       |
| is_answered     | BOOLEAN                 | whether bot produced a helpful answer      |
| created_at      | TIMESTAMPTZ             | default `now()`                            |

### 3.4 documents

Knowledge-base sources ingested into the RAG pipeline.

| Column        | Type               | Notes                                          |
|---------------|--------------------|------------------------------------------------|
| id            | UUID PK            |                                                |
| title         | TEXT NOT NULL      | document title                                |
| source_type   | TEXT NOT NULL      | `website` \| `pdf` \| `faq` \| `text` \| ...   |
| source_url    | TEXT               | original location                             |
| category      | TEXT               | e.g. `admissions`, `fees`, `programmes`        |
| content       | TEXT               | full source text                               |
| chunked       | BOOLEAN            | has chunks been generated                      |
| created_at    | TIMESTAMPTZ        | default `now()`                                |
| updated_at    | TIMESTAMPTZ        | default `now()`                                |

### 3.5 chunks

Sentence/section-level chunks with embeddings for retrieval.

| Column        | Type                 | Notes                                    |
|---------------|----------------------|------------------------------------------|
| id            | UUID PK              |                                          |
| document_id   | UUID FK → documents.id | `ON DELETE CASCADE`                    |
| content       | TEXT NOT NULL        | chunk text                               |
| embedding     | VECTOR(1536)         | OpenAI `text-embedding-ada-002` output   |
| metadata      | JSONB                | section headings, page numbers, etc.     |
| created_at    | TIMESTAMPTZ          | default `now()`                          |

### 3.6 feedback

User-reported quality of bot answers.

| Column         | Type                 | Notes                       |
|----------------|----------------------|-----------------------------|
| id             | UUID PK              |                             |
| message_id     | BIGINT FK → messages.id |                          |
| conversation_id| UUID FK → conversations.id |                        |
| rating         | SMALLINT             | 1–5                        |
| comment        | TEXT                 | optional                    |
| created_at     | TIMESTAMPTZ          | default `now()`             |

### 3.7 refresh_tokens

Long-lived tokens for dashboard sessions (optional).

| Column     | Type                 | Notes                      |
|------------|----------------------|----------------------------|
| id         | UUID PK              |                            |
| user_id    | UUID FK → users.id   | `ON DELETE CASCADE`        |
| token      | TEXT NOT NULL        | hashed refresh token       |
| expires_at | TIMESTAMPTZ          |                            |
| created_at | TIMESTAMPTZ          | default `now()`            |

### 3.8 Indexes

- `users.phone` unique
- `users.student_id` unique
- `messages(conversation_id, created_at)`
- `chunks.embedding` (pgvector HNSW/IVFFlat) — cosine distance
- `documents(category, source_type)`

## 4. API Endpoints

Base URL: `http://localhost:8000` (prod: Render / `BACKEND_URL`). All endpoints return JSON unless stated otherwise.

### 4.1 Public

| Method | Path                 | Auth | Description                        |
|--------|----------------------|------|------------------------------------|
| GET    | `/`                  | —    | API info                           |
| GET    | `/health`            | —    | Health check                       |
| GET    | `/webhook/whatsapp`   | —    | Meta webhook verification (challenge) |
| POST   | `/webhook/whatsapp`   | —    | Meta WhatsApp message webhook         |

### 4.2 Auth

| Method | Path                    | Auth   | Description                          |
|--------|-------------------------|--------|--------------------------------------|
| POST   | `/auth/otp/request`     | —      | Request 6-digit OTP by phone         |
| POST   | `/auth/otp/verify`      | —      | Verify OTP, returns JWT tokens       |
| GET    | `/auth/me`              | Bearer | Current user profile                 |
| POST   | `/auth/refresh`         | —      | Exchange refresh token for new JWT   |

### 4.3 Conversations

| Method | Path                  | Auth   | Description                        |
|--------|-----------------------|--------|------------------------------------|
| GET    | `/conversations`      | Bearer | List current user's conversations  |
| POST   | `/conversations`      | Bearer | Start a new conversation           |
| GET    | `/conversations/{id}` | Bearer | Get conversation + messages        |
| PATCH  | `/conversations/{id}` | Bearer | Update (close/archive)             |

### 4.4 Messages

| Method | Path                          | Auth   | Description                    |
|--------|-------------------------------|--------|--------------------------------|
| POST   | `/messages`                   | Bearer | Send user message, get bot reply |
| POST   | `/messages/{id}/feedback`     | Bearer | Rate an answer (1–5 + comment) |

### 4.5 Documents (Knowledge Base)

Admin-managed, used by the RAG pipeline.

| Method | Path                        | Auth    | Description                       |
|--------|-----------------------------|---------|-----------------------------------|
| GET    | `/documents`                | Bearer  | List documents                   |
| POST   | `/documents`                | Bearer  | Ingest new document              |
| GET    | `/documents/{id}`           | Bearer  | Document detail                  |
| DELETE | `/documents/{id}`           | Bearer  | Remove document + chunks         |
| POST   | `/documents/{id}/rechunk`   | Bearer  | Re-chunk and re-embed            |
| GET    | `/documents/{id}/chunks`    | Bearer  | List chunks for a document       |

### 4.6 Ask / Search

| Method | Path        | Auth   | Description                              |
|--------|-------------|--------|------------------------------------------|
| POST   | `/ask`      | —      | Direct RAG query, returns answer + sources |
| GET    | `/search`   | —      | Keyword/vector hybrid search, top-k chunks |

### 4.7 Admin (Dashboard)

| Method | Path                                 | Auth              | Description                |
|--------|--------------------------------------|-------------------|----------------------------|
| GET    | `/admin/dashboard/stats`             | Bearer + admin    | Overview metrics          |
| GET    | `/admin/users`                       | Bearer + admin    | List users                 |
| PATCH  | `/admin/users/{id}/role`             | Bearer + admin    | Promote/demote role       |
| GET    | `/admin/conversations`               | Bearer + admin    | All conversations         |
| GET    | `/admin/analytics/messages`          | Bearer + admin    | Message volume analytics  |
| GET    | `/admin/analytics/feedback`          | Bearer + admin    | Feedback aggregation      |

## 5. RAG Knowledge Base Sources

### 5.1 Sources

Initial corpus for Limkokwing University, ingested via the `rag/` pipeline:

| # | Source                      | Type      | Notes                                  |
|---|-----------------------------|-----------|----------------------------------------|
| 1 | Official website (limkokwing.net) | HTML scrape | pages: home, about, admissions      |
| 2 | Student Handbook             | PDF       | student life, rules, support services  |
| 3 | Prospectus / Admissions      | PDF       | entry requirements, how to apply       |
| 4 | Programme / Course Catalog   | HTML/PDF  | all faculties, programmes, durations   |
| 5 | Fee Schedule                 | PDF/HTML  | tuition fees, deposits, payment plans  |
| 6 | Academic Calendar            | PDF       | semesters, breaks, key dates           |
| 7 | Exam Timetable               | PDF/HTML  | exam period instructions               |
| 8 | Policies FAQ                 | Text      | attendance, plagiarism, conduct       |
| 9 | Campus & Facilities          | HTML      | locations, accommodation, IT, library  |
| 10 | Top-question FAQ             | Text      | curated from WhatsApp analytics        |
| 11 | Degree Verification / Transcripts | Internal | access-controlled, staff only       |
| 12 | Announcements / News         | HTML      | recent updates, events                 |

### 5.2 Ingestion Pipeline

1. **Collect** — scraper/parser pulls HTML/PDF/text per source.
2. **Clean** — strip navigation/boilerplate, normalize Unicode.
3. **Chunk** — split into ~500-char chunks with ~50-char overlap (per section/semantic boundary).
4. **Embed** — `OpenAI text-embedding-ada-002` → 1536-dim vectors.
5. **Store** — insert into `chunks` (pgvector) linked to `documents`.

### 5.3 Retrieval (Hybrid)

- Vector search (cosine, pgvector) + keyword search (Postgres FTS) with weighted fusion.
- Top-k (default 5) chunks per query; optional metadata filters (`category`, `source_type`).
- Re-ranking (e.g. RRF) applied in Phase 3 tuning.
- Answer generated by `gpt-3.5-turbo` with citations returned to the client.

## 6. Phases

- **Phase 1** — Design finalization (this doc) + repo/monorepo setup
- **Phase 2** — Backend skeleton, auth/OTP, webhook plumbing, dashboard base
- **Phase 3** — RAG pipeline (ingestion, retrieval, answering)
- **Phase 4** — Admin dashboard + analytics + go-live polish