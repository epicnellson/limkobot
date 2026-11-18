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
