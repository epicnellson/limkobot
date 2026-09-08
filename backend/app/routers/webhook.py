from fastapi import APIRouter, Request, Response

from app.services.rag_service import answer

router = APIRouter(tags=["webhook"])


def _twiml_messaging(text: str) -> Response:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{text}</Message></Response>"
    )
    return Response(content=xml, media_type="text/xml")


@router.post("/webhook/twilio")
async def twilio_webhook(request: Request) -> Response:
    form = await request.form()
    body = form.get("Body", "").strip()

    if not body:
        reply = (
            "Hi! I'm LimkoBot. Ask me about admissions, programmes, fees, "
            "or campus services at Limkokwing University."
        )
    else:
        reply = answer(body)

    return _twiml_messaging(reply)