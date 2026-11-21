import re

from app.services.rag_service import answer as rag_answer

WELCOME_TEXT = (
    "Welcome to Limkokwing University! How can I help you today?\n\n"
    "Reply a number:\n"
    "1 = Fees\n"
    "2 = Exam schedule\n"
    "3 = Registration\n"
    "4 = Programmes\n"
    "5 = Talk to support\n\n"
    "Or type your question and I will do my best to help."
)

MENU_HINT = "Reply 1 = Fees, 2 = Exam schedule, 3 = Registration, 4 = Programmes, 5 = Support."

GREETING_WORDS = ("hi", "hey")

RULE_INTENTS = {
    "greeting": {
        "keywords": ("hi", "hello", "hey", "good morning", "good afternoon", "good day"),
        "reply": WELCOME_TEXT,
    },
    "fees": {
        "keywords": ("fee", "tuition", "cost", "price", "payment"),
        "reply": (
            "Fees depend on your programme and campus. Reply with a programme name "
            "for the current fee schedule, or DOCUMENTS for the full fee table."
        ),
    },
    "admissions": {
        "keywords": ("admission", "apply", "enrol", "enroll", "application", "entry"),
        "reply": (
            "To apply, visit the admissions page on limkokwing.net or reply ADMISSIONS "
            "and I will send the entry requirements."
        ),
    },
    "programmes": {
        "keywords": ("programme", "program", "course", "degree", "diploma", "faculty", "study"),
        "reply": (
            "We offer diplomas, degrees and postgraduate programmes. Tell me the faculty "
            "you are interested in and I will list the options."
        ),
    },
    "exam_schedule": {
        "keywords": ("exam", "timetable", "test schedule"),
        "reply": (
            "Exam schedule: 2026 final exams run 8-19 June. Reply with your programme "
            "and I will narrow down the paper timetable."
        ),
    },
    "registration": {
        "keywords": ("register", "registration", "semester", "enrolment", "enrollment"),
        "reply": (
            "Registration is done online through the student portal before semester start. "
            "Reply REGISTRATION for the step-by-step guide."
        ),
    },
    "documents": {
        "keywords": ("document", "transcript", "prospectus", "certificate", "letter"),
        "reply": (
            "To request a document (transcript, admission letter, prospectus), reply with "
            "the exact document name and your student or application number."
        ),
    },
    "support": {
        "keywords": ("help", "support", "contact", "where are you", "location", "human"),
        "reply": (
            "I can help with fees, exams, registration and programmes. "
            "For anything else, reply SUPPORT and a staff member will follow up."
        ),
    },
    "thanks": {
        "keywords": ("thank", "thanks", "appreciate"),
        "reply": "You're welcome! Is there anything else I can help you with? " + MENU_HINT,
    },
    "bye": {
        "keywords": ("bye", "goodbye", "see you"),
        "reply": "Goodbye and good luck with your studies at Limkokwing University!",
    },
}

NEGATIVE_WORDS = ("bad", "anger", "complaint", "disappointed", "annoyed", "refund", "terrible")

NEGATIVE_SCORE = -0.8
FLAG_SEVERITY = "high"

MENU_TRIGGERS = ("menu", "start", "main menu", "options", "0")

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
            "Support: a staff member will follow up on your question. Meanwhile, "
            "you can reply 1 = Fees, 2 = Exam schedule, 3 = Registration, 4 = Programmes."
        ),
    },
}


def _matches(text: str, keyword: str) -> bool:
    if keyword in GREETING_WORDS:
        return re.search(rf"\b{re.escape(keyword)}\b", text) is not None
    return keyword in text


def select_reply(message_text: str) -> tuple[str, str | None, str]:
    """Return (reply, intent_type, routing) for a message."""
    text = message_text.lower().strip()

    menu_option = MENU.get(text)
    if menu_option:
        return menu_option["reply"], menu_option["intent"], "menu"

    if text in MENU_TRIGGERS:
        return WELCOME_TEXT, "menu", "menu"

    for name, rule in RULE_INTENTS.items():
        if any(_matches(text, keyword) for keyword in rule["keywords"]):
            return rule["reply"], name, "rule"

    return rag_answer(message_text), None, "rag"


def is_negative(message_text: str) -> bool:
    text = message_text.lower()
    return any(word in text for word in NEGATIVE_WORDS)
