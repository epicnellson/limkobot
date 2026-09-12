# LimkoBot — Action Plan: Fixes & Next Steps
**For: Emmanuel (Role A) — to execute now, and to brief Moses + Bernard**
**Using: OpenCode CLI for code generation, GitHub for tracking**

Today is 8 September 2026 — you're a few days past the original v0.0 deadline (Sep 5), which is normal and fine, but it makes reassigning Moses and Bernard **today** more urgent, not less. Do the steps in order.

---

## STEP 1 — Reassign GitHub Issues (do this first, 10 minutes, no code)

The current assignment has Emmanuel owning 7 of 12 issues and Moses/Bernard idle until week 8–11. Fix it in GitHub directly — no OpenCode needed for this part.

### Move these 2 issues from Emmanuel → Bernard:
| Issue | From | To |
|---|---|---|
| Set up Supabase database | Emmanuel | **Bernard** |
| Finalize database schema | Emmanuel | **Bernard** |

### Create 3 new issues today:

| New Issue | Assignee | Milestone |
|---|---|---|
| Set up RAG pipeline skeleton (LangChain project structure, no real documents yet) | **Moses** | v0.0 |
| Set up admin dashboard skeleton (React app, empty pages, no real data) | **Bernard** | v0.0 |
| Prototype RAG answering on 5 mock Q&A pairs | **Moses** | v0.1 |

### Final corrected assignment table:

| # | Issue | Assignee | Milestone |
|---|---|---|---|
| 1 | Set up backend skeleton | Emmanuel | v0.0 ✅ done |
| 2 | Set up Supabase database | **Bernard** | v0.0 |
| 13 | Set up RAG pipeline skeleton | **Moses** | v0.0 |
| 14 | Set up admin dashboard skeleton | **Bernard** | v0.0 |
| 3 | Finalize database schema | **Bernard** | v0.1 |
| 4 | Finalize API contract | Emmanuel | v0.1 |
| 15 | Prototype RAG on mock Q&A | **Moses** | v0.1 |
| 5 | Set up WhatsApp Cloud API webhook | Emmanuel | v0.2 |
| 6 | Implement OTP authentication | Emmanuel | v0.2 |
| 7 | Implement rule-based menu | Emmanuel | v0.2 |
| 8 | Build RAG pipeline (real documents) | Moses | v0.3 |
| 9 | Implement sentiment analysis | Moses | v0.3 |
| 10 | Build WhatsApp Flow (or fallback — see Step 4) | Emmanuel | v0.4 |
| 11 | Finalize admin dashboard | Bernard | v0.4 |
| 12 | User testing (sample size capped at 5 without business verification — see note below) | Bernard + all | v0.9 |

**Note on issue #12:** WhatsApp's dev-mode limit is 5 verified recipient numbers without completing Business Verification (which you're skipping — see Meta setup notes). Update the issue description to reflect a realistic sample size (5 real testers, rotated if needed) rather than the original 20–30 target, and note this constraint explicitly in your dissertation's evaluation/limitations section.

Send this message to your group now:

> "Reorganized the board so everyone has work starting this week. Moses — you're on RAG pipeline setup, no dependency on my backend. Bernard — you're on Supabase account + DB schema + dashboard skeleton, also independent. Check your new issues."

---

## STEP 2 — Fix the Database Schema (matches your submitted ERD, not DeepSeek's version)

Run this directly in Supabase's SQL Editor. This replaces DeepSeek's `users/messages/documents` schema with the exact entities from your proposal's ERD (`Student`, `ConversationLog`, `DocumentRequest`, `KnowledgeDocument`, `SentimentFlag`, `AdminUser`).

```sql
-- Enable vector search
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE students (
    student_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(150) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    programme VARCHAR(100),
    otp_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE admin_users (
    admin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    role VARCHAR(50),
    email VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE knowledge_documents (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    embedding_vector VECTOR(384),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversation_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    intent_type VARCHAR(50),
    sentiment_score DECIMAL(5,4),
    "timestamp" TIMESTAMP DEFAULT NOW()
);

CREATE TABLE document_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    doc_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    generated_at TIMESTAMP
);

CREATE TABLE sentiment_flags (
    flag_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_id UUID REFERENCES conversation_logs(log_id) ON DELETE CASCADE,
    severity VARCHAR(20),
    reviewed_by UUID REFERENCES admin_users(admin_id),
    resolved BOOLEAN DEFAULT FALSE
);

-- Junction table for the N:M "retrieved" relationship in your ERD
CREATE TABLE conversation_retrieved_docs (
    log_id UUID REFERENCES conversation_logs(log_id) ON DELETE CASCADE,
    doc_id UUID REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE,
    PRIMARY KEY (log_id, doc_id)
);

-- Indexes
CREATE INDEX idx_conv_student ON conversation_logs(student_id);
CREATE INDEX idx_docreq_student ON document_requests(student_id);
CREATE INDEX idx_flag_log ON sentiment_flags(log_id);
```

**Bernard's task:** run this, then insert 1–2 mock students to confirm it works, then update `docs/SYSTEM_SPECS.md` to match — delete DeepSeek's old schema description from that file if you already added it.

---

## STEP 3 — Decide the LLM Provider Now (don't let this surprise anyone in week 9)

Your proposal budgets $20–40 for LLM usage — that's fine, but OpenAI requires a funded, card-linked account. Confirm one of these **today**:

**Option A — Keep GPT-4o-mini:** confirm out loud in your group chat whose card funds the OpenAI account, and that they're reimbursed from the group's shared costs.

**Option B — Switch to Google Gemini's free tier** (genuinely free, no card required for the free quota) — simpler for a student budget. If you go this route, tell Moses now, since it changes the RAG pipeline's LLM client code.

Whichever you pick, add it to `.env.example` clearly:
```bash
# Pick ONE:
OPENAI_API_KEY=your_key_here
# OR
GOOGLE_API_KEY=your_key_here
LLM_PROVIDER=openai   # or "gemini"
```

---

## STEP 4 — WhatsApp Business API (Meta Cloud API) Setup — replaces Twilio entirely

You've switched from Twilio to the real WhatsApp Business Platform (Meta's Cloud API). This is actually a good change — it removes the middleman, and Meta's own free tier is genuinely generous (1,000 free service conversations/month, no card required to start in development mode). It also means WhatsApp Flows are natively supported through Meta's own Flow Builder, so the earlier concern about Twilio not cleanly supporting Flows goes away — but the setup steps are different from what DeepSeek described, so update accordingly.

### 4.1 — Accounts needed (do this before any webhook code)
1. A Meta Developer account at developers.facebook.com
2. A Meta App (type: Business), with the **WhatsApp** product added
3. In development mode, Meta gives you a **free test phone number** and up to 5 verified recipient numbers — enough for your whole group plus a couple of early testers, no business verification needed yet
4. From the app dashboard, collect:
   - `WHATSAPP_ACCESS_TOKEN` (temporary 24h token to start; generate a permanent System User token before user testing in week 12)
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_BUSINESS_ACCOUNT_ID`
   - A `WEBHOOK_VERIFY_TOKEN` you make up yourself (any random string — Meta echoes it back to confirm you own the webhook)

### 4.2 — Update `.env.example` (replace any Twilio variables)
```bash
WHATSAPP_ACCESS_TOKEN=your_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_BUSINESS_ACCOUNT_ID=your_waba_id_here
WEBHOOK_VERIFY_TOKEN=make_up_a_random_string_here
```

### 4.3 — One important structural difference from Twilio
Meta's Cloud API requires your webhook endpoint to handle **two** methods, not one:
- `GET /webhook/whatsapp` — Meta calls this once when you register the webhook URL, sending a `hub.challenge` query param you must echo back to verify ownership
- `POST /webhook/whatsapp` — actual incoming messages, as JSON (not form-encoded like Twilio), with a nested structure (`entry[0].changes[0].value.messages[0]`)

Flag this to Emmanuel directly: any webhook code already written against Twilio's flat form-encoded payload (`From`, `Body`) needs rewriting, not just patching — the parsing logic is genuinely different.

### 4.4 — WhatsApp Flows
Since Flows are now natively available, Emmanuel can build the real guided transcript/fee-receipt flow through Meta's Flow Builder (in the Meta Business Manager UI) rather than the plain-text fallback suggested earlier. Still worth timeboxing: give it a defined 2–3 day spike, and fall back to the numbered-message approach below if it's eating more time than that this close to your Phase 4 deadline.

**Fallback (only if Flow Builder setup runs long):**
1. Bot: "Request a document — reply 1 for Transcript, 2 for Fee Receipt"
2. Bot: "Confirm: [Name], [Student ID] — reply YES to confirm"
3. Bot: "Request submitted. You'll receive it within 24 hours."

### 4.5 — Update your proposal/pitch materials for consistency
Your submitted proposal and pptx tech-stack slide both say "WhatsApp Business API (Twilio sandbox)." Since you've moved to the real Meta Cloud API directly, update that line before your next submission or presentation — or, if you'd rather not touch the already-submitted proposal, note the switch explicitly as a documented decision in your dissertation's "Challenges Encountered and Solutions" section (per your department's template) — examiners read a justified pivot as good engineering judgement, not as a problem, as long as it's written down rather than left as a silent mismatch.

### 4.6 — Unblocking "Configure Webhooks" (the step that trips everyone up)

Meta requires a live, public HTTPS server before it will accept your Callback URL — you can't fill this in until something is actually running. Fastest path:

1. Run the minimal webhook below locally (`uvicorn main:app --reload --port 8000`):
```python
from fastapi import FastAPI, Request
import os

app = FastAPI()
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "limkobot_dev_2026")

@app.get("/webhook/whatsapp")
async def verify(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return {"error": "verification failed"}, 403

@app.post("/webhook/whatsapp")
async def receive(request: Request):
    body = await request.json()
    print(body)
    return {"status": "ok"}
```
2. Expose it with `ngrok http 8000` — gives a temporary public URL for testing today.
3. In Meta's dashboard: Callback URL = `https://<ngrok-id>.ngrok-free.app/webhook/whatsapp`, Verify token = any string you invent (must match `WEBHOOK_VERIFY_TOKEN`).
4. Click Verify and Save — Meta hits your GET endpoint, you echo back `hub.challenge`, it goes green.
5. **This week:** deploy the same webhook to Render and swap the Callback URL to the permanent Render URL — ngrok's free URL changes on every restart, which breaks things right before user testing if left in place.

**Skip for now:** registering your own phone number (the free test number covers dev mode), and adding a payment method (only needed for business-initiated messages, not your MVP's reply-only flow — 1,000 free service conversations/month covers you).

---

Since you're using OpenCode to speed things up, here are ready-to-paste prompts for each person's next task. Run these from inside the relevant folder (`backend/`, `rag/`, `dashboard/`) so OpenCode has the right context.

### Emmanuel — finalize API contract (v0.1)
```
Read the existing backend/routers structure. Create an OpenAPI-style
markdown table in docs/API_CONTRACT.md listing every endpoint LimkoBot
needs: /webhook/whatsapp (GET, for Meta's verification challenge),
/webhook/whatsapp (POST, incoming messages via Meta's WhatsApp Cloud
API — JSON payload, not form-encoded), /auth/otp/request (POST),
/auth/otp/verify (POST), /chat/ask (POST, routes to rule-based or RAG),
/documents/request (POST), /documents/status (GET),
/admin/knowledge-base (POST, upload doc), /admin/flags (GET, list
sentiment flags). For each, list method, auth required (yes/no),
request body fields, and response fields. Match field names to the
students/conversation_logs/document_requests/sentiment_flags schema
in docs/SYSTEM_SPECS.md.
```

### Emmanuel — WhatsApp Cloud API webhook (v0.2)
```
In backend/routers/webhook.py, implement two handlers for Meta's
WhatsApp Cloud API (not Twilio):
1. GET /webhook/whatsapp — read query params hub.mode, hub.verify_token,
   hub.challenge. If hub.verify_token matches WEBHOOK_VERIFY_TOKEN from
   .env, return hub.challenge as plain text with status 200. Otherwise
   return 403.
2. POST /webhook/whatsapp — parse the JSON body. Messages arrive at
   body["entry"][0]["changes"][0]["value"]["messages"][0], with the
   sender's number at ["from"] and text at ["text"]["body"]. Extract
   these and pass to a process_message(from_number, message_text)
   function (stub it for now). Return status 200 immediately per
   Meta's requirements (they expect a fast ack, not a synchronous
   response — replies are sent via a separate outgoing API call, not
   in the webhook response body, unlike Twilio's TwiML).
Also create a send_message(to_number, text) helper that POSTs to
https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages
with the access token as a Bearer header, per Meta's send-message API
shape.
```

### Moses — RAG pipeline skeleton (v0.0)
```
Set up a Python project in /rag with LangChain. Create:
1. ingestion.py — a function that takes a text file, chunks it
   (RecursiveCharacterTextSplitter, chunk_size=500, overlap=50), and
   returns chunks (don't embed yet, just structure).
2. retrieval.py — a stub function `answer_question(question: str,
   documents: list) -> str` that will later call an embedding model
   and vector search — for now just return a placeholder response so
   the interface is defined.
3. requirements.txt with langchain, and note the LLM provider is
   TBD (OpenAI or Gemini — check with Emmanuel before hardcoding).
Do not connect to Supabase yet — this is a local, mock-data skeleton
only, per issue #13.
```

### Moses — prototype on mock Q&A (v0.1, after skeleton)
```
Using the rag/ skeleton, create 5 mock question-answer pairs about a
fictional university policy (e.g. "What's the grade appeal deadline?").
Write them to rag/mock_data/sample_docs.txt. Wire ingestion.py to chunk
this file and retrieval.py to do simple keyword-based retrieval (no
embeddings yet) so we can test the end-to-end shape before adding a
real vector store. Add a test script that asks each of the 5 questions
and prints the retrieved chunk.
```

### Bernard — Supabase schema (v0.0/v0.1)
```
I have a SQL migration for our Supabase project (students, admin_users,
knowledge_documents, conversation_logs, document_requests,
sentiment_flags, conversation_retrieved_docs — see the SQL in this
action plan doc). Run it against our Supabase project, then write a
Python test script backend/test_db.py that connects using the supabase
client, inserts one mock student, and confirms the row can be read
back. Also update docs/SYSTEM_SPECS.md to describe this schema,
replacing any old schema description there.
```

### Bernard — admin dashboard skeleton (v0.0)
```
Set up a React + Vite project in /dashboard. Create empty pages for:
Login, Dashboard (overview stats), Knowledge Base (list/upload
documents), Flagged Conversations (list of sentiment flags awaiting
review), Student Lookup. Use React Router. No real API calls yet —
use hardcoded placeholder data in each page so the UI is navigable.
Keep styling minimal (Tailwind is fine) — this is a skeleton, not a
final design.
```

### Emmanuel — OTP authentication (v0.2, issue #6)
```
Implement OTP-based student authentication in backend/app/routers/auth.py
and backend/app/services/auth_service.py:

1. POST /auth/otp/request — accepts {"phone_number": str}. Looks up the
   student in the `students` table by phone_number (create the row if
   it doesn't exist yet, with otp_verified=False). Generates a random
   6-digit code, stores it with a 5-minute expiry (use an otps table:
   columns id, student_id, code, expires_at, used — add this table to
   the schema.sql migration if it isn't there yet). Sends the code via
   the WhatsApp send_message() helper already built in whatsapp_service.py
   (not email — we're sending the OTP over WhatsApp itself, since that's
   the channel the student is already in). Returns {"status": "sent"}.

2. POST /auth/otp/verify — accepts {"phone_number": str, "code": str}.
   Checks the otps table for a matching, unexpired, unused code for
   that student. If valid: mark it used, set students.otp_verified=True,
   issue a JWT (use python-jose, HS256, read JWT_SECRET_KEY from env,
   24-hour expiry, payload = {"student_id": ...}). Return
   {"status": "verified", "token": "..."}. If invalid or expired, return
   401 with a clear error message.

3. Add a dependency function get_current_student() that reads the JWT
   from an Authorization: Bearer header, validates it, and returns the
   student record — use this to protect any future endpoint that needs
   auth (e.g. /documents/request will use this later).

4. Write unit tests for both endpoints: request with a new number,
   verify with correct code, verify with wrong code, verify with
   expired code. Add the otps table migration to the same schema file
   Bernard is running in Supabase — flag in your PR description that
   Bernard needs to re-run the migration to pick up the new table.

Do not implement the rule-based menu or webhook routing logic that
calls this — just the auth endpoints and JWT logic themselves.
```

---

## Remaining Roadmap — What's Left, In Order

You're currently mid-Phase 2 (v0.2 — Core MVP). Here's everything from here to submission, in the order to tackle it:

### Now → this week: finish v0.2 (Emmanuel)
1. ✅ Webhook (done)
2. **OTP auth** — use the prompt above (issue #6)
3. **Rule-based menu** (issue #7) — once OTP works, build the simple menu: student sends a number 1–4, bot replies with fees/exam schedule/registration info from hardcoded or Supabase-stored text. This is the last v0.2 item — once it's done, tag `v0.2` in GitHub and merge to `main`.

### In parallel, this week: Moses and Bernard start their v0.0/v0.1 work
Use the OpenCode prompts already in this doc (Moses — RAG pipeline skeleton and prototype; Bernard — Supabase schema and dashboard skeleton). They don't need to wait for your v0.2 to finish.

### Weeks 8–10 (v0.3 — Intelligence Layer)
4. **Real RAG pipeline** (issue #8, Moses) — swap the mock-data prototype for real Limkokwing documents (whatever you've collected — course catalogue, fee schedule, policy handbook). Connect to Supabase's pgvector instead of keyword matching.
5. **Sentiment analysis** (issue #9, Moses) — VADER or a similarly lightweight classifier, scoring each incoming message, writing to `conversation_logs.sentiment_score`, and inserting a row into `sentiment_flags` when a message crosses your distress threshold.
6. **Emmanuel's job here:** wire the webhook's `process_message()` stub (still a TODO from the earlier webhook prompt) to actually call: OTP check → rule-based menu OR Moses's RAG function → sentiment check → log to `conversation_logs` → send reply.

**Test against your 85% intent-accuracy target at the end of this phase** — this is your checkpoint to know if you need extra tuning time before Phase 4.

### Week 11 (v0.4 — Feature Complete)
7. **WhatsApp Flow or fallback** (issue #10, Emmanuel) — per Step 4.4 above: try Meta's Flow Builder for the transcript/fee-receipt request, timeboxed to 2–3 days; fall back to the numbered-message sequence if it's running long.
8. **Finalize admin dashboard** (issue #11, Bernard) — wire the skeleton pages to real API calls: list flagged conversations from `sentiment_flags`, show knowledge base documents, basic student lookup.
9. **Freeze new features after this week.** Everything from here is testing and polish.

### Weeks 12–13 (v0.9 — Release Candidate)
10. Unit + integration tests across all three of your areas.
11. **User testing** (issue #12) — with your realistic 5-tester sample (see note above). Collect task completion, accuracy ratings, satisfaction score.
12. Deploy the real backend to Render so testers use the live system, not localhost — swap your ngrok webhook URL for the permanent Render URL in Meta's dashboard at this point.
13. Bug-fixing sprint driven by GitHub Issues labeled `bug`.

### Weeks 14–15 (v1.0 — Final Submission)
14. Analyze evaluation results against your objectives' success metrics.
15. Write the evaluation, limitations (mention the WhatsApp dev-mode 5-tester constraint here), and future-work sections.
16. Finalize dissertation document and slide deck.
17. Tag `v1.0` and submit.

---

1. Reassign the GitHub issues (Step 1) — 10 minutes
2. Run the corrected SQL schema in Supabase, or hand it to Bernard (Step 2)
3. Decide OpenAI vs Gemini and tell Moses (Step 3)
4. Set up your Meta Developer app + WhatsApp product, update `.env.example`, and brief Emmanuel that webhook code needs Meta's GET/POST shape, not Twilio's (Step 4)
5. Send Moses and Bernard their OpenCode prompts (Step 5) so they start today, not in week 8
6. Update the "Twilio sandbox" line in your submitted proposal/pptx tech stack, or log the switch in your dissertation's Challenges section (Step 4.5)
