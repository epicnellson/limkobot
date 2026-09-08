# LimkoBot Backend

FastAPI service powering the WhatsApp chatbot and admin dashboard.

## Structure

```
backend/
├── main.py                 # FastAPI app entrypoint (uvicorn main:app)
├── requirements.txt
├── app/
│   ├── config.py           # Settings loaded from .env
│   ├── database.py         # SQLAlchemy engine/session
│   ├── dependencies.py     # get_current_user / require_admin
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── routers/            # API route modules
│   └── services/           # Twilio, email, auth, RAG (stubs)
└── tests/
```

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows  |  source venv/bin/activate  (macOS/Linux)
pip install -r requirements.txt
cp .env.example .env         # then fill in credentials
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

Interactive docs: http://127.0.0.1:8000/docs

## Test & Lint

```bash
pytest
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## Status

Phase 2 skeleton: auth/OTP, WhatsApp webhook, conversations, messages
(RAG stub answer), documents CRUD, and admin endpoints.