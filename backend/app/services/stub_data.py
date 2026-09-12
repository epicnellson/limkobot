import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone

from app.services.auth_service import generate_otp
from app.services.rag_service import answer as rag_answer

logger = logging.getLogger(__name__)

_lock = threading.Lock()

# Field names and semantics mirror Bernard's Supabase schema
# (students, conversation_logs, document_requests, sentiment_flags,
#  knowledge_documents) as defined in docs/SYSTEM_SPECS.md Section 3.
_students = {}
_conversation_logs = {}
_document_requests = {}
_sentiment_flags = {}
_knowledge_documents = {}
_otps = {}

OTP_TTL_SECONDS = 5 * 60

DOC_TYPES = (
    "prospectus",
    "fee_schedule",
    "transcript",
    "student_handbook",
    "academic_calendar",
    "other",
)

RULE_INTENTS = {
    "greeting": {
        "keywords": ("hi", "hello", "hey", "good morning", "good afternoon", "good day"),
        "reply": "Hello! Welcome to Limkokwing University. How can I help you today?",
    },
    "fees": {
        "keywords": ("fee", "tuition", "cost", "price", "payment"),
        "reply": (
            "Fees depend on your programme and campus. Reply with a programme name "
            "for the current fee schedule, or a document request for the full table."
        ),
    },
    "admissions": {
        "keywords": ("admission", "apply", "enrol", "application", "entry"),
        "reply": (
            "To apply, visit the admissions page on limkokwing.net or reply ADMISSIONS "
            "and I will send the entry requirements."
        ),
    },
    "programmes": {
        "keywords": ("programme", "course", "degree", "diploma", "study"),
        "reply": (
            "We offer diplomas, degrees and postgraduate programmes. Tell me the faculty "
            "you are interested in and I will list the options."
        ),
    },
    "help": {
        "keywords": ("help", "support", "contact", "where are you", "location"),
        "reply": "For help, reply with a keyword like FEES, ADMISSIONS, PROGRAMMES or DOCUMENTS.",
    },
}

NEGATIVE_WORDS = ("bad", "anger", "complaint", "disappointed", "annoyed", "refund", "terrible")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def reset() -> None:
    """Clear the in-memory store (tests)."""
    with _lock:
        _students.clear()
        _conversation_logs.clear()
        _document_requests.clear()
        _sentiment_flags.clear()
        _knowledge_documents.clear()
        _otps.clear()


def get_or_create_student(phone_number: str) -> dict:
    with _lock:
        student = _students.get(phone_number)
        if student is None:
            student = {
                "student_id": _new_id(),
                "phone_number": phone_number,
                "full_name": None,
                "programme": None,
                "otp_verified": False,
                "created_at": _now(),
            }
            _students[phone_number] = student
        return student


def get_student_by_id(student_id: str) -> dict | None:
    with _lock:
        for student in _students.values():
            if student["student_id"] == student_id:
                return student
    return None


def request_otp(phone_number: str) -> dict:
    """Create/fetch the student and store a fresh 6-digit code (5-min expiry).

    Returns {"student": ..., "code": ...} so the router can deliver the code.
    """
    student = get_or_create_student(phone_number)
    now = datetime.now(timezone.utc)
    code = generate_otp()
    with _lock:
        _otps[student["student_id"]] = {
            "code": code,
            "expires_at": (now + timedelta(seconds=OTP_TTL_SECONDS)).isoformat(),
            "used": False,
            "created_at": now.isoformat(),
        }
    return {"student": student, "code": code}


def verify_otp(phone_number: str, code: str) -> dict | None:
    """Validate an unexpired, unused OTP. On success marks it used and sets
    students.otp_verified=True, returning the student. Returns None otherwise.
    """
    student = _students.get(phone_number)
    if student is None:
        return None
    with _lock:
        otp = _otps.get(student["student_id"])
        if otp is None:
            return None
        expires_at = datetime.fromisoformat(otp["expires_at"])
        if otp["used"] or otp["code"] != code or expires_at < datetime.now(timezone.utc):
            return None
        otp["used"] = True
    student["otp_verified"] = True
    return student


def get_active_otp(phone_number: str) -> dict | None:
    """Return a copy of the current OTP row for a phone number (tests)."""
    student = _students.get(phone_number)
    if student is None:
        return None
    with _lock:
        otp = _otps.get(student["student_id"])
        return dict(otp) if otp else None


def force_expire_otp(phone_number: str) -> None:
    """Backdate the current OTP's expiry so it reads as expired (tests)."""
    student = _students.get(phone_number)
    if student is None:
        return
    with _lock:
        otp = _otps.get(student["student_id"])
        if otp is not None:
            otp["expires_at"] = (
                datetime.now(timezone.utc) - timedelta(seconds=1)
            ).isoformat()


def _log_message(
    student_id: str, message_text: str, intent_type=None, sentiment_score=None
) -> dict:
    log = {
        "log_id": _new_id(),
        "student_id": student_id,
        "message_text": message_text,
        "intent_type": intent_type,
        "sentiment_score": sentiment_score,
        "timestamp": _now(),
    }
    with _lock:
        _conversation_logs[log["log_id"]] = log
    return log


def add_flag(log: dict, severity: str) -> dict:
    flag = {
        "flag_id": _new_id(),
        "log_id": log["log_id"],
        "severity": severity,
        "reviewed_by": None,
        "resolved": False,
    }
    with _lock:
        _sentiment_flags[flag["flag_id"]] = flag
    return flag


def ask(phone_number: str, message_text: str) -> dict:
    student = get_or_create_student(phone_number)
    text = message_text.lower()

    user_message = _log_message(student["student_id"], message_text)
    bot_reply = rag_answer(message_text)
    intent_type = None
    routing = "rag"

    for name, rule in RULE_INTENTS.items():
        if any(keyword in text for keyword in rule["keywords"]):
            intent_type = name
            routing = "rule"
            bot_reply = rule["reply"]
            break

    for word in NEGATIVE_WORDS:
        if word in text:
            flag = add_flag(user_message, "high")
            logger.info("Created sentiment flag %s on log %s", flag["flag_id"], user_message["log_id"])
            user_message["sentiment_score"] = -0.8
            break

    bot_message = _log_message(
        student["student_id"], bot_reply, intent_type=intent_type
    )

    return {
        "user_message": user_message,
        "bot_message": bot_message,
        "sources": [],
        "routing": routing,
    }


def create_document_request(phone_number: str, doc_type: str) -> dict:
    student = get_or_create_student(phone_number)
    request = {
        "request_id": _new_id(),
        "student_id": student["student_id"],
        "doc_type": doc_type,
        "status": "pending",
        "generated_at": None,
    }
    with _lock:
        _document_requests[request["request_id"]] = request
    return request


def list_document_requests(phone_number: str) -> list[dict]:
    student = get_or_create_student(phone_number)
    with _lock:
        return [
            request
            for request in _document_requests.values()
            if request["student_id"] == student["student_id"]
        ]


def add_knowledge_document(title: str, category: str | None, content: str) -> dict:
    document = {
        "doc_id": _new_id(),
        "title": title,
        "category": category,
        "embedded": False,
        "updated_at": _now(),
    }
    with _lock:
        _knowledge_documents[document["doc_id"]] = document
    return document


def list_flags(resolved: bool | None = None, severity: str | None = None) -> list[dict]:
    flags = list(_sentiment_flags.values())
    if resolved is not None:
        flags = [flag for flag in flags if flag["resolved"] is resolved]
    if severity is not None:
        flags = [flag for flag in flags if flag["severity"] == severity]

    result = []
    for flag in flags:
        log = _conversation_logs.get(flag["log_id"])
        result.append(
            {
                "flag_id": flag["flag_id"],
                "log_id": flag["log_id"],
                "severity": flag["severity"],
                "reviewed_by": flag["reviewed_by"],
                "resolved": flag["resolved"],
                "message_text": log["message_text"] if log else None,
                "timestamp": log["timestamp"] if log else None,
            }
        )
    return result