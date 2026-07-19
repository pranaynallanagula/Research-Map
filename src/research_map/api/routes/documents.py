from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from research_map.core.config import Settings, get_settings
from research_map.db.models import DocumentStatus
from research_map.db.repositories import DocumentRepository, ProjectRepository
from research_map.db.session import get_db
from research_map.ingestion.storage import (
    StoredUpload,
    UploadValidationError,
    store_pdf,
)

router = APIRouter(
    prefix="/projects/{project_id}/documents",
    tags=["documents"],
)


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    original_filename: str
    content_hash: str
    status: DocumentStatus


def _remove_upload(upload: StoredUpload) -> None:
    if upload.created:
        upload.path.unlink(missing_ok=True)


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: UUID,
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentUploadResponse:
    """Store a PDF and create its initial document record."""

    project = ProjectRepository(db).get(project_id)
    if project is None:
        await file.close()
        raise HTTPException(status_code=404, detail="Research project not found")

    try:
        stored_upload = await store_pdf(file, project_id, settings)
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    filename = Path(file.filename or "research-paper.pdf").name
    title = Path(filename).stem or "Untitled research paper"
    document_repository = DocumentRepository(db)

    try:
        document = document_repository.create(
            project_id=project_id,
            title=title,
            original_filename=filename,
            content_hash=stored_upload.content_hash,
            source_uri=stored_upload.path.as_posix(),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        _remove_upload(stored_upload)
        raise HTTPException(
            status_code=409,
            detail="This document is already in the research project",
        ) from exc
    except Exception:
        db.rollback()
        _remove_upload(stored_upload)
        raise

    return DocumentUploadResponse.model_validate(document)
