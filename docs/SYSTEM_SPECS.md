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

All primary keys are UUIDs (`gen_random_uuid()`). Timestamps use `TIMESTAMP DEFAULT NOW()`. Embeddings are stored as `VECTOR(384)` using the pgvector extension.

### 3.1 students
| Column | Type | Notes |
|---|---|---|
| student_id | UUID PK | |
| full_name | VARCHAR(150) NOT NULL | |
| phone_number | VARCHAR(20) UNIQUE NOT NULL | WhatsApp number |
| programme | VARCHAR(100) | |
| otp_verified | BOOLEAN DEFAULT FALSE | |
| created_at | TIMESTAMP DEFAULT NOW() | |

### 3.2 admin_users
| Column | Type | Notes |
|---|---|---|
| admin_id | UUID PK | |
| name | VARCHAR(150) NOT NULL | |
| role | VARCHAR(50) | |
| email | VARCHAR(150) UNIQUE NOT NULL | |

### 3.3 knowledge_documents
| Column | Type | Notes |
|---|---|---|
| doc_id | UUID PK | |
| title | VARCHAR(255) NOT NULL | |
| category | VARCHAR(100) | |
| embedding_vector | VECTOR(384) | |
| updated_at | TIMESTAMP DEFAULT NOW() | |

### 3.4 conversation_logs
| Column | Type | Notes |
|---|---|---|
| log_id | UUID PK | |
| student_id | UUID FK → students | ON DELETE CASCADE |
| message_text | TEXT NOT NULL | |
| intent_type | VARCHAR(50) | |
| sentiment_score | DECIMAL(5,4) | |
| timestamp | TIMESTAMP DEFAULT NOW() | |

### 3.5 document_requests
| Column | Type | Notes |
|---|---|---|
| request_id | UUID PK | |
| student_id | UUID FK → students | ON DELETE CASCADE |
| doc_type | VARCHAR(50) NOT NULL | |
| status | VARCHAR(20) DEFAULT 'pending' | |
| generated_at | TIMESTAMP | |

### 3.6 sentiment_flags
| Column | Type | Notes |
|---|---|---|
| flag_id | UUID PK | |
| log_id | UUID FK → conversation_logs | ON DELETE CASCADE |
| severity | VARCHAR(20) | |
| reviewed_by | UUID FK → admin_users | |
| resolved | BOOLEAN DEFAULT FALSE | |

### 3.7 conversation_retrieved_docs (junction table)
| Column | Type | Notes |
|---|---|---|
| log_id | UUID FK → conversation_logs | ON DELETE CASCADE |
| doc_id | UUID FK → knowledge_documents | ON DELETE CASCADE |

PK is (log_id, doc_id).

### 3.8 Indexes
- `conversation_logs(student_id)`
- `document_requests(student_id)`
- `sentiment_flags(log_id)`

> **Note (RLS):** Row Level Security is not yet enabled — access is currently server-side only via the `service_role` key. To be added before real student data enters the system (user-testing phase).
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