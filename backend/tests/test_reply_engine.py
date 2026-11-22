from app.services import reply_engine


def test_menu_digit_returns_menu_routing():
    reply, intent, routing = reply_engine.select_reply("1")

    assert routing == "menu"
    assert intent == "fees"
    assert "Fees (2026)" in reply


def test_rule_keyword_returns_rule_routing():
    reply, intent, routing = reply_engine.select_reply("What programmes do you offer?")

    assert routing == "rule"
    assert intent == "programmes"
    assert "diplomas" in reply


def test_unknown_message_falls_back_to_rag():
    reply, intent, routing = reply_engine.select_reply("tell me a joke")

    assert routing == "rag"
    assert intent is None
    assert "still learning" in reply


def test_is_negative_matches_complaint_words():
    assert reply_engine.is_negative("I am disappointed with the service") is True
    assert reply_engine.is_negative("Thank you very much") is False


def test_welcome_text_lists_menu_options():
    assert "Welcome to Limkokwing University" in reply_engine.WELCOME_TEXT
    assert "1 = Fees" in reply_engine.WELCOME_TEXT


def test_menu_word_returns_welcome_text():
    reply, intent, routing = reply_engine.select_reply("MENU")

    assert routing == "menu"
    assert intent == "menu"
    assert "1 = Fees" in reply


def test_greeting_uses_word_boundaries():
    _, _, routing = reply_engine.select_reply("this is fine")

    assert routing == "rag"


def test_llm_fallback_used_when_available(monkeypatch):
    monkeypatch.setattr(reply_engine, "llm_answer", lambda _text: "Krio answer")

    reply, intent, routing = reply_engine.select_reply("Aw di tin de go naw?")

    assert reply == "Krio answer"
    assert intent is None
    assert routing == "llm"


def test_krio_greeting_matches_rule():
    _, intent, routing = reply_engine.select_reply("Kushɛ, aw yu du")

    assert routing == "rule"
    assert intent == "greeting"


def test_krio_thanks_matches_rule():
    _, intent, _ = reply_engine.select_reply("Tɛnki papa")

    assert intent == "thanks"


def test_krio_question_prefers_llm_over_fee_rule(monkeypatch):
    monkeypatch.setattr(reply_engine, "llm_answer", lambda _text: "Krio fee answer")

    reply, intent, routing = reply_engine.select_reply("Aw much di fees naw?")

    assert reply == "Krio fee answer"
    assert intent is None
    assert routing == "llm"


def test_english_fee_question_stays_rule():
    _, intent, routing = reply_engine.select_reply("How much are the fees?")

    assert intent == "fees"
    assert routing == "rule"


def test_looks_krio_detection():
    assert reply_engine._looks_krio("Aw yu du, mi want know") is True
    assert reply_engine._looks_krio("How much are the fees?") is False
