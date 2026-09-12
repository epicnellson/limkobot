from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Chunk, Document
from app.schemas.document import DocumentCreate, DocumentOut
from app.schemas.document_request import DocumentRequestCreate, DocumentRequestOut
from app.services import stub_data

router = APIRouter(prefix="/documents", tags=["documents"])


def _get_document(document_id: UUID, db: Session) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return document


@router.post("/request", response_model=DocumentRequestOut, status_code=201)
def request_document(payload: DocumentRequestCreate) -> dict:
    return stub_data.create_document_request(payload.phone_number, payload.doc_type)


@router.get("/status", response_model=list[DocumentRequestOut])
def document_request_status(phone_number: str) -> list[dict]:
    return stub_data.list_document_requests(phone_number)


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.post("", response_model=DocumentOut, status_code=201)
def create_document(
    payload: DocumentCreate, db: Session = Depends(get_db)
) -> Document:
    document = Document(
        title=payload.title,
        source_type=payload.source_type,
        source_url=payload.source_url,
        category=payload.category,
        content=payload.content,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: UUID, db: Session = Depends(get_db)) -> Document:
    return _get_document(document_id, db)


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: UUID, db: Session = Depends(get_db)) -> None:
    document = _get_document(document_id, db)
    db.delete(document)
    db.commit()


@router.post("/{document_id}/rechunk", response_model=dict)
def rechunk_document(document_id: UUID, db: Session = Depends(get_db)) -> dict:
    _get_document(document_id, db)
    return {"detail": "Chunking and embedding will be implemented in Phase 3"}


@router.get("/{document_id}/chunks", response_model=list[dict])
def list_chunks(document_id: UUID, db: Session = Depends(get_db)) -> list[dict]:
    _get_document(document_id, db)
    chunks = (
        db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.created_at).all()
    )
    return [
        {
            "id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "content": chunk.content,
            "created_at": chunk.created_at.isoformat(),
        }
        for chunk in chunks
    ]