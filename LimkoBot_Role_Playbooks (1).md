# LimkoBot — Role Playbooks
**Initial stage → final stage, by person**

Roles (confirmed): **Emmanuel = Role A (Backend & WhatsApp Integration)** · **Moses = Role B (AI/RAG & Sentiment)** · **Bernard = Role C (Data, Dashboard & QA)**

Detailed OpenCode prompts for specific tasks already exist in `LimkoBot_Action_Plan.md` — this doc tells each person *what* to do and *when*; cross-reference that file for the exact prompt text where noted.

---

## EMMANUEL — Role A: Backend & WhatsApp Integration

**You own:** the webhook, authentication, the rule-based menu, the WhatsApp Flow, deployment, and — critically — you're the one who wires everyone else's work together into a single working pipeline.

### Phase 0 — Foundations (Week 1)
1. Create the GitHub repo, branch protection on `main`/`dev`, Projects board, `CONTRIBUTING.md`.
2. Set up your Meta Developer account, create the Meta App, add the WhatsApp product, get your test number and 5 verified recipient slots.
3. Collect and store (don't commit) `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`, invent `WEBHOOK_VERIFY_TOKEN`.
4. Build the minimal webhook (GET verification + POST message receipt), run it locally, expose with ngrok, verify green in Meta's dashboard.
5. **Do not set up the database** — that's Bernard's. Leave `.env.example` with placeholder `SUPABASE_*` vars for him to fill.

### Phase 1 — Design (Weeks 2–3)
6. Write `docs/API_CONTRACT.md` — every endpoint, method, auth requirement, request/response fields. Use the OpenCode prompt for this already in the Action Plan doc.
7. Wait for Bernard's schema to land before wiring real DB calls — build your route handlers with a stubbed data layer in the meantime so you're not blocked.

### Phase 2 — Core MVP (Weeks 4–7)
8. **OTP authentication** — use the Action Plan's OTP prompt. Sends the code over WhatsApp itself, issues a JWT, exposes `get_current_student()` for protecting later endpoints.
9. **Rule-based menu** — once OTP works, build the numbered-option menu (1 = fees, 2 = exam schedule, etc.) reading from Supabase once Bernard's schema is live.
10. Tag `v0.2`, merge to `main`.

### Phase 3 — Intelligence Layer (Weeks 8–10)
11. This is your main integration job: wire the webhook's `process_message()` stub to actually call, in order: OTP check → rule-based menu **or** Moses's RAG function → sentiment check (also Moses's) → log to `conversation_logs` → send reply.
12. You don't build the RAG or sentiment logic yourself — you consume the functions Moses hands you. Agree on function signatures with him early in this phase so you're not blocked waiting.

### Phase 4 — Feature Complete (Week 11)
13. Build the WhatsApp Flow for the transcript/fee-receipt request through Meta's Flow Builder — timebox to 2–3 days, fall back to the numbered-message sequence (already specced in the Action Plan doc) if it's running long.
14. **Deploy the backend to Render.** Swap your webhook's Callback URL in Meta's dashboard from the ngrok URL to the permanent Render URL — do this now, not during user testing.
15. Feature freeze after this week.

### Phase 5 — Testing (Weeks 12–13)
16. Support user testing: monitor logs during test sessions, fix any bugs that surface in real time, keep uptime steady.
17. Fix bugs from the `bug`-labeled GitHub issues as they're filed by Bernard or Moses.

### Phase 6 — Submission (Weeks 14–15)
18. Write the System Architecture and System Development sections of the dissertation (Chapter/Section covering backend design, webhook flow, auth).
19. Prepare and rehearse the live demo — you're the one most likely to be running it live, since you own the end-to-end flow.
20. Final deploy check the day before submission — confirm Render instance is live and Meta webhook still points at it (Render's free tier can spin down on inactivity — send it a request the morning of any demo to wake it up).

---

## MOSES — Role B: AI / RAG & Sentiment

**You own:** the retrieval-augmented answering engine, and the sentiment-analysis module that detects student distress.

### Phase 0 — Foundations (Week 1)
1. Set up the `/rag` project skeleton with LangChain — use the OpenCode prompt already in the Action Plan doc (chunking + retrieval stub, no real embeddings yet).
2. **Decide the LLM provider with Emmanuel this week** — OpenAI GPT-4o-mini (needs a funded card) or Google Gemini's free tier. Get your API key once decided.
3. You don't touch Supabase directly yet — this phase is local, mock-data only.

### Phase 1 — Design (Weeks 2–3)
4. Prototype RAG on 5 mock Q&A pairs with simple keyword retrieval (no embeddings) — proves the interface shape before adding real infrastructure. Prompt already in the Action Plan doc.
5. Read up on pgvector basics now, since you'll be querying Bernard's vector store directly in Phase 3 — no need to wait idle.

### Phase 2 — Core MVP (Weeks 4–7)
6. While Emmanuel builds auth/menu, start collecting or requesting the real Limkokwing documents (course catalogue, fee schedule, academic policy handbook) you'll need for Phase 3 — this is a good use of time now rather than waiting.
7. Decide your sentiment approach (VADER is the simplest, no training data needed) and get a basic scorer working on sample text locally.

### Phase 3 — Intelligence Layer (Weeks 8–10, your main phase)
8. Swap the mock prototype for real documents: chunk them, embed them, store embeddings in Bernard's `knowledge_documents.embedding_vector` column via pgvector.
9. Build the real retrieval + generation chain: given a question, retrieve top-k chunks, generate a grounded answer via your chosen LLM.
10. Build the sentiment module: score every incoming message, write the score to `conversation_logs.sentiment_score`, and insert a row into `sentiment_flags` when a message crosses your distress threshold.
11. **Hand off clean function signatures to Emmanuel** — e.g. `answer_question(text: str) -> str` and `score_sentiment(text: str) -> dict` — so he can wire them into the webhook without needing to understand your internals.
12. Test against the 85% intent-accuracy target using a set of 50–100 real student-style questions — this is your Phase 3 checkpoint, not something to leave until week 13.

### Phase 4 — Feature Complete (Week 11)
13. Tune RAG accuracy and the sentiment threshold based on Phase 3 test results — reduce both wrong answers and false-positive distress flags.
14. Support Emmanuel if the WhatsApp Flow needs any AI-generated content (unlikely, but be available).

### Phase 5 — Testing (Weeks 12–13)
15. Run your accuracy test set again post-integration and log real numbers — this becomes your evaluation chapter's core data.
16. Analyze the sentiment module's false-positive rate from real user-testing conversations.
17. Fix any AI-side bugs filed during testing.

### Phase 6 — Submission (Weeks 14–15)
18. Write the RAG and sentiment methodology + evaluation sections of the dissertation — your test-set numbers are the evidence here.
19. Contribute the RAG-specific parts of the literature review (you already have the citations from the proposal — Adesua, the RAG survey, Lang & Gürpinar) if that section needs expanding for the final report.

---

## BERNARD — Role C: Data, Dashboard & QA

**You own:** the database (now that Emmanuel's handed it off correctly), the admin/counsellor dashboard, and coordinating testing.

### Phase 0 — Foundations (Week 1)
1. **Create the Supabase project now** (Emmanuel deleted his — this is correctly your task). Run the SQL migration from `LimkoBot_Action_Plan.md` (students, admin_users, knowledge_documents, conversation_logs, document_requests, sentiment_flags, conversation_retrieved_docs).
2. Insert 1–2 mock students, write `backend/test_db.py` to confirm the connection works (prompt already in the Action Plan doc).
3. Set up the React + Vite dashboard skeleton — empty pages for Login, Dashboard, Knowledge Base, Flagged Conversations, Student Lookup, using hardcoded placeholder data for now.

### Phase 1 — Design (Weeks 2–3)
4. Write up the schema in `docs/SYSTEM_SPECS.md`, replacing any leftover DeepSeek schema description.
5. Cross-check Emmanuel's `docs/API_CONTRACT.md` field names against your actual schema column names — catch mismatches now, not during integration.
6. **Note:** once Emmanuel's OTP prompt adds the new `otps` table, re-run the migration to pick it up.

### Phase 2 — Core MVP (Weeks 4–7)
7. Keep building out the dashboard pages against mock data while Emmanuel works on auth/menu.
8. Manually test Emmanuel's OTP and webhook as they land in PRs — you're a reviewer on his pull requests, not just building in isolation.

### Phase 3 — Intelligence Layer (Weeks 8–10)
9. Wire the dashboard's Flagged Conversations page to real data from Moses's `sentiment_flags` table, and the Knowledge Base page to `knowledge_documents`.
10. Start planning user-testing logistics now, not in week 12: **you're capped at 5 verified WhatsApp recipient numbers** (dev-mode limit, since you're skipping business verification) — decide who those 5 testers are, and whether you'll rotate testers between rounds.

### Phase 4 — Feature Complete (Week 11)
11. Finalize the dashboard — all pages wired to real endpoints, basic styling pass.
12. Deploy the dashboard (Vercel or Netlify free tier both work well for a React/Vite app).
13. Confirm your 5 test recipients are ready — get them to message the test number in advance so there's no last-minute WhatsApp linking delay.

### Phase 5 — Testing (Weeks 12–13)
14. **Lead user testing.** Run sessions with your 5 testers: task completion (did they successfully get an answer / request a document?), accuracy rating, satisfaction score (1–5).
15. Run integration and system tests across the whole pipeline — not just your own components.
16. File bugs as GitHub issues labeled `bug` as you find them during testing; don't just fix silently — the issue trail is your dissertation evidence.

### Phase 6 — Submission (Weeks 14–15)
17. Compile the evaluation results into tables (accuracy, latency, satisfaction) — this is the core data for the Product Evaluation / Testing Results chapter.
18. Write the Testing Strategy and User Evaluation sections of the dissertation.
19. Help assemble the appendices — screenshots of the dashboard, test case tables, sample database schema.

---

## Shared responsibilities (all three, ongoing)

- **Code review:** every PR needs one approval from someone other than the author — rotate this, don't let it default to whoever's fastest to respond.
- **Weekly check-in:** a 15-minute sync each week to confirm you're not blocked on each other — Phase 3 especially, since Emmanuel depends on Moses's function signatures and Bernard's schema simultaneously.
- **Dissertation writing is shared, not delegated entirely to whoever owns a section** — each person drafts their own area, but all three should read the whole document before submission so no one is surprised by what's in it.
