from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, auth, chat, conversations, documents, messages, webhook

app = FastAPI(
    title=settings.APP_NAME,
    description="Hybrid RAG WhatsApp Chatbot for Limkokwing University",
    version=settings.APP_VERSION,
)

# CORS for admin dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(documents.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"message": "LimkoBot API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}