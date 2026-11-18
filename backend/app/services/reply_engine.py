"""Deterministic reply selection for WhatsApp and chat messages.

Shared by the in-memory stub store and the database-backed store so both
paths answer identically.
"""

from app.services.rag_service import answer as rag_answer

WELCOME_TEXT = (
    "Welcome to Limkokwing University! How can I help you today?\n\n"
    "Reply a number:\n"
    "1 = Fees\n"
    "2 = Exam schedule\n"
    "3 = Registration\n"
    "4 = Programmes\n\n"
    "Or type your question and I will do my best to help."
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

NEGATIVE_SCORE = -0.8
FLAG_SEVERITY = "high"

MENU = {
    "1": {
        "intent": "fees",
        "reply": (
            "Fees (2026): application fee USD 100; tuition varies by programme and campus. "
            "Reply with your programme for the exact schedule, "
            "or DOCUMENTS to request the fee table."
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


def select_reply(message_text: str) -> tuple[str, str | None, str]:
    """Return (reply, intent_type, routing) for a message."""
    text = message_text.lower()

    menu_option = MENU.get(text.strip())
    if menu_option:
        return menu_option["reply"], menu_option["intent"], "menu"

    for name, rule in RULE_INTENTS.items():
        if any(keyword in text for keyword in rule["keywords"]):
            return rule["reply"], name, "rule"

    return rag_answer(message_text), None, "rag"


def is_negative(message_text: str) -> bool:
    text = message_text.lower()
    return any(word in text for word in NEGATIVE_WORDS)
