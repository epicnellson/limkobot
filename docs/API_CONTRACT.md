# LimkoBot — API Contract (Phase 1)

Definitive contract for all LimkoBot endpoints: method, auth requirement, request fields, and response fields.
Field names match the implemented Supabase schema in [`docs/SYSTEM_SPECS.md`](./SYSTEM_SPECS.md) Section 3
(`students`, `admin_users`, `knowledge_documents`, `conversation_logs`, `document_requests`,
`sentiment_flags`, `conversation_retrieved_docs`).

- Base URL (dev): `http://localhost:8000` · (prod): `$BACKEND_URL`
- All endpoints return JSON unless stated otherwise.
- Auth: `Authorization: Bearer <access_token>` for endpoints marked **Yes**.
- OTP is 6 digits; phone numbers are E.164 (`+260...`).

## Endpoint overview

| # | Method | Path                 | Auth | Description                                                  |
|---|--------|----------------------|------|--------------------------------------------------------------|
| 1 | GET    | `/webhook/whatsapp`  | No   | Meta verification challenge                                   |
| 2 | POST   | `/webhook/whatsapp`  | No   | Incoming messages, Meta WhatsApp Cloud API (JSON body)       |
| 3 | POST   | `/auth/otp/request`  | No   | Request 6-digit OTP by phone                                  |
| 4 | POST   | `/auth/otp/verify`   | No   | Verify OTP → JWT access token                                 |
| 5 | POST   | `/chat/ask`          | No   | Answer a question (routes to rule-based or RAG)               |
| 6 | POST   | `/documents/request` | No   | Student requests a document (fee schedule, transcript, …)     |
| 7 | GET    | `/documents/status`  | No   | List a student's document requests + status                   |
| 8 | POST   | `/admin/knowledge-base` | Yes | Admin uploads a knowledge-base document (RAG ingest)        |
| 9 | GET    | `/admin/flags`       | Yes  | List sentiment flags raised on messages                       |

---

## 1. `GET /webhook/whatsapp` — Meta verification

Meta `GET`s this URL when you click **Verify and save** in the app dashboard. Echo the challenge to prove the endpoint is ours.

Auth: **No**

Query params:

| Field            | Type   | Required | Description                          |
|------------------|--------|----------|--------------------------------------|
| `hub.mode`       | string | Yes      | Must be `subscribe`                  |
| `hub.verify_token` | string | Yes    | Must equal `WEBHOOK_VERIFY_TOKEN` (env) |
| `hub.challenge`  | string | Yes      | Opaque value echoed back              |

Response — **200** `text/plain`: the challenge value verbatim. **403** on mismatch.

---

## 2. `POST /webhook/whatsapp` — incoming message

Meta `POST`s a **JSON** payload (not form-encoded) per event. Returns `200` immediately; processing is asynchronous.

Auth: **No** (signature validation `X-Hub-Signature-256` is a TODO — Meta verifies the source via our `hub.verify_token`/subscription).

Representative request body (only fields we read):

| Field (path)                                    | Type   | Description                          |
|-------------------------------------------------|--------|--------------------------------------|
| `entry[0].id`                                    | string | Business account ID                  |
| `entry[0].changes[0].value.messaging_product`    | string | `whatsapp`                           |
| `entry[0].changes[0].value.metadata.display_phone_number` | string | Sender display number        |
| `entry[0].changes[0].value.metadata.phone_number_id`      | string | Our phone number ID        |
| `entry[0].changes[0].value.contacts[0].profile.name`      | string | Sender profile name        |
| `entry[0].changes[0].value.contacts[0].wa_id`             | string | Sender WhatsApp ID         |
| `entry[0].changes[0].value.messages[0].from`              | string | Sender number (E.164)      |
| `entry[0].changes[0].value.messages[0].id`                | string | Message ID (`wamid...`)    |
| `entry[0].changes[0].value.messages[0].timestamp`         | string | Unix timestamp             |
| `entry[0].changes[0].value.messages[0].type`              | string | `text` (only type handled) |
| `entry[0].changes[0].value.messages[0].text.body`         | string | Message text               |

The `statuses[]` variant has **no** `messages[]` — webhook must return `200` and do nothing.

Response — **200** `text/plain` `OK`. Never error to Meta (retries).

Side effects (schema): upsert `students` on `phone_number`; each turn logged to `conversation_logs`
(`message_text`, `intent_type`, `sentiment_score`); route to `process_message(from, body)`.

---

## 3. `POST /auth/otp/request` — request OTP

Auth: **No**

Request body (schema `OTPRequest`):

| Field   | Type   | Required | Constraint                | Persists to              |
|---------|--------|----------|---------------------------|--------------------------|
| `phone` | string | Yes      | E.164 (`^\+\d{10,15}$`)  | `students.phone_number`  |
| `email` | string | No       | —                         | OTP delivery channel     |

Response — **200**:

| Field                | Type | Example                 |
|----------------------|------|-------------------------|
| `detail`             | string | `"OTP sent"`          |
| `expires_in_minutes` | int  | `5`                     |

Server-side: generate 6-digit code, set expiry (5 min), mark `students.otp_verified=false` until verify.

---

## 4. `POST /auth/otp/verify` — verify OTP → JWT

Auth: **No**

Request body (schema `OTPVerify`):

| Field   | Type   | Required | Constraint                  |
|---------|--------|----------|-----------------------------|
| `phone` | string | Yes      | E.164                       |
| `code`  | string | Yes      | Exactly 6 digits            |

Response — **200** (schema `Token`):

| Field          | Type   | Description                        |
|----------------|--------|------------------------------------|
| `access_token` | string | JWT (HS256, `sub` = student id)   |
| `token_type`   | string | `bearer`                           |
| `expires_in`   | int    | Seconds (JWT TTL × 60)             |

Sets `students.otp_verified=true`. Errors: **400** invalid/expired code, **404** unknown phone.

---

## 5. `POST /chat/ask` — ask a question

Routes to rule-based answering (greetings, FAQ keywords) or RAG retrieval. Both turns are logged to
`conversation_logs` (one row per message; there is **no** session table in the schema).

Auth: **No** (invoked from the WhatsApp webhook; identity = `phone_number`). Dashboard sessions use `/messages` (Bearer).

Request body:

| Field          | Type   | Required | Description                            |
|----------------|--------|----------|----------------------------------------|
| `phone_number` | string | Yes      | E.164 sender (looked up in `students`) |
| `message_text` | string | Yes      | Question text (1–4000 chars)           |

Response — **200**:

| Field          | Type     | Description                                       |
|----------------|----------|---------------------------------------------------|
| `user_message` | object   | Logged user turn (see `ChatMessage` below)        |
| `bot_message`  | object   | Logged bot turn (same shape)                      |
| `sources`      | array    | RAG citations `{id, title, category, source_url, score}` (empty for rule-based) |
| `routing`      | string   | `rule` \| `rag`                                   |

`ChatMessage` (per `conversation_logs` row):

| Field            | Type    | Description                              |
|------------------|---------|------------------------------------------|
| `log_id`         | string  | `conversation_logs.log_id`               |
| `student_id`     | string  | `students.student_id`                    |
| `sender`         | string  | `user` \| `bot` — client-facing only; **not a column** (both directions are rows in `conversation_logs`) |
| `message_text`   | string  | `conversation_logs.message_text`         |
| `intent_type`    | string  | `conversation_logs.intent_type` (null if unknown) |
| `sentiment_score`| number  | `conversation_logs.sentiment_score` (e.g. `-0.8` for flagged); null otherwise |
| `timestamp`      | string  | `conversation_logs.timestamp`            |

`intent_type` + negative scoring come from the rule classifier; RAG routing falls through to retrieval (Phase 3).

---

## 6. `POST /documents/request` — request a document

Student asks the university for a document (prospectus, fee schedule, transcript, handbook). Creates a row in `document_requests`.

Auth: **No** (phone-identified via WhatsApp session).

Request body:

| Field          | Type   | Required | Description                            |
|----------------|--------|----------|----------------------------------------|
| `phone_number` | string | Yes      | E.164 requester (`students.phone_number`) |
| `doc_type`     | string | Yes      | `prospectus` \| `fee_schedule` \| `transcript` \| `student_handbook` \| `academic_calendar` \| `other` |

Response — **201** (`document_requests` row):

| Field         | Type    | Description                                |
|---------------|---------|--------------------------------------------|
| `request_id`  | string  | `document_requests.request_id`             |
| `student_id`  | string  | `document_requests.student_id`             |
| `doc_type`    | string  | requested type                             |
| `status`      | string  | `pending` (initial)                        |
| `generated_at`| string  | `null` until fulfilled                     |

---

## 7. `GET /documents/status` — check document requests

Auth: **No** (phone identity)

Query params:

| Field          | Type   | Required | Description                            |
|----------------|--------|----------|----------------------------------------|
| `phone_number` | string | Yes      | E.164; resolved to `students.student_id` |

Response — **200**: array of `document_requests` rows (empty `[]` if none):

| Field          | Type    | Description                             |
|----------------|---------|-----------------------------------------|
| `request_id`   | string  | Request ID                              |
| `student_id`   | string  | Owning student                          |
| `doc_type`     | string  | `prospectus`, …                          |
| `status`       | string  | `pending` \| `fulfilled` \| `rejected`  |
| `generated_at` | string  | `null` while pending                     |

---

## 8. `POST /admin/knowledge-base` — upload knowledge-base doc

Admin drops a document into the KB for RAG ingestion. Creates a `knowledge_documents` row
(embedding generation happens in Phase 3).

Auth: **Yes** — Bearer, **role must be `admin`** (`admin_users.role`).

Request — multipart `form-data`:

| Field      | Type              | Required | Description                                  |
|------------|-------------------|----------|----------------------------------------------|
| `file`     | file              | Yes      | PDF / .txt / .md / .html (max 10 MB)         |
| `title`    | string            | Yes      | `knowledge_documents.title`                  |
| `category` | string            | No       | e.g. `admissions`, `fees`, `programmes`      |

Response — **201** (`knowledge_documents` row):

| Field         | Type    | Description                               |
|---------------|---------|-------------------------------------------|
| `doc_id`      | string  | `knowledge_documents.doc_id`              |
| `title`       | string  |                                           |
| `category`    | string  | nullable                                  |
| `embedded`    | boolean | `false` until Phase-3 embedding pass (`embedding_vector` null) |
| `updated_at`  | string  | ISO-8601                                  |

Errors: **401** no/invalid token, **403** non-admin, **413** file too large.

---

## 9. `GET /admin/flags` — list sentiment flags

Flags raised on `conversation_logs` by rule or model (negative/escalation content), for the dashboard moderation queue.

Auth: **Yes** — Bearer, role `admin`.

Query params:

| Field        | Type   | Required | Description                          |
|--------------|--------|----------|--------------------------------------|
| `resolved`   | bool   | No       | Filter `true`/`false`; default all   |
| `severity`   | string | No       | Filter `low` \| `medium` \| `high`   |

Response — **200**: array of flags (empty `[]`). `message_text`/`timestamp` are **joined from** the referenced `conversation_logs` row:

| Field          | Type    | Description                                   |
|----------------|---------|-----------------------------------------------|
| `flag_id`      | string  | `sentiment_flags.flag_id`                     |
| `log_id`       | string  | `sentiment_flags.log_id` (FK → `conversation_logs`) |
| `severity`     | string  | `low` \| `medium` \| `high`                   |
| `reviewed_by`  | string  | `admin_users.admin_id` or `null`              |
| `resolved`     | boolean | `false` until admin action                    |
| `message_text` | string  | joined from `conversation_logs.message_text`  |
| `timestamp`    | string  | joined from `conversation_logs.timestamp`     |

---

## Error reference

| Code | Body shape (`{"detail": "..."}`)                        | When                                  |
|------|---------------------------------------------------------|---------------------------------------|
| 400  | Invalid/expired OTP, bad payload                         | `otp/verify`                          |
| 401  | Missing/invalid JWT                                     | `admin/*`                             |
| 403  | Wrong verify token OR non-admin on admin route          | webhook GET, `admin/*`                |
| 404  | Phone/user/conversation/message unknown                 | `otp/verify`, `chat/ask`, `messages`  |
| 413  | Uploaded knowledge-base file too large                  | `admin/knowledge-base`                |
| 422  | Pydantic validation failure (field/type/pattern)        | Any JSON body                         |

## Mapping to SYSTEM_SPECS tables

| Endpoint(s)                                    | Table(s) touched                       |
|------------------------------------------------|----------------------------------------|
| `GET/POST /webhook/whatsapp`                   | `students`, `conversation_logs`        |
| `POST /auth/otp/request`, `/auth/otp/verify`   | `students`                             |
| `POST /chat/ask`                               | `conversation_logs`, `sentiment_flags` |
| `POST /documents/request`, `GET /documents/status` | `document_requests`               |
| `POST /admin/knowledge-base`                   | `knowledge_documents`                  |
| `GET /admin/flags`                             | `sentiment_flags`, `conversation_logs` |