import logging
import threading
import uuid
from datetime import datetime, timezone

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

# Numbered menu: student sends a single digit, bot answers with that option.
MENU = {
    "1": {
        "intent": "fees",
        "reply": (
            "Fees (2026): application fee USD 100; tuition varies by programme and campus. "
            "Reply with your programme for the exact schedule, or DOCUMENTS to request the fee table."
        ),
    },
    "2": {
        "intent": "exam_schedule",
        "reply": (
            "Exam schedule: 2026 final exams run 8-19 June. "
            "Check faculty notice boards or reply with your programme for the paper timetable."
        ),
    },
    "3": {
        "intent": "registration",
        "reply": (
            "Registration: returning students register online through the student portal "
            "before semester start. Reply REGISTRATION for a step-by-step guide."
        ),
    },
    "4": {
        "intent": "programmes",
        "reply": (
            "Programmes: diplomas, degrees and postgraduate courses across computing, design, "
            "business, communication and architecture. Reply with a faculty for the full list."
        ),
    },
    "5": {
        "intent": "help",
        "reply": (
            "How can I help? Reply a number: 1 = Fees, 2 = Exam schedule, "
            "3 = Registration, 4 = Programmes."
        ),
    },
}


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


def _log_message(student_id: str, message_text: str, intent_type=None, sentiment_score=None) -> dict:
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

    menu_option = MENU.get(text.strip())
    if menu_option:
        intent_type = menu_option["intent"]
        routing = "menu"
        bot_reply = menu_option["reply"]
    else:
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