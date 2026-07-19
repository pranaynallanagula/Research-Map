import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_map.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    ResearchProject,
    ResearchQuery,
)


def _validate_pagination(limit: int, offset: int) -> None:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("offset cannot be negative")


class ProjectRepository:
    """Persistence operations for research projects."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, name: str, description: str | None = None) -> ResearchProject:
        project = ResearchProject(name=name, description=description)
        self.session.add(project)
        self.session.flush()
        return project

    def get(self, project_id: uuid.UUID) -> ResearchProject | None:
        return self.session.get(ResearchProject, project_id)

    def list(self, limit: int = 50, offset: int = 0) -> list[ResearchProject]:
        _validate_pagination(limit, offset)
        statement = (
            select(ResearchProject)
            .order_by(ResearchProject.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())


class DocumentRepository:
    """Persistence operations for uploaded research documents."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        project_id: uuid.UUID,
        title: str,
        original_filename: str,
        content_hash: str,
        source_uri: str | None = None,
        abstract: str | None = None,
        publication_year: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Document:
        document = Document(
            project_id=project_id,
            title=title,
            original_filename=original_filename,
            content_hash=content_hash,
            source_uri=source_uri,
            abstract=abstract,
            publication_year=publication_year,
            metadata_json=metadata if metadata is not None else {},
        )
        self.session.add(document)
        self.session.flush()
        return document

    def get(self, document_id: uuid.UUID) -> Document | None:
        return self.session.get(Document, document_id)

    def list_for_project(
        self,
        project_id: uuid.UUID,
        status: DocumentStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        _validate_pagination(limit, offset)
        statement = select(Document).where(Document.project_id == project_id)
        if status is not None:
            statement = statement.where(Document.status == status)
        statement = (
            statement.order_by(Document.created_at.desc()).offset(offset).limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def set_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
    ) -> Document | None:
        document = self.get(document_id)
        if document is None:
            return None
        document.status = status
        self.session.flush()
        return document


@dataclass(frozen=True, slots=True)
class ChunkInput:
    """Values needed to persist one document chunk."""

    ordinal: int
    content: str
    page_start: int | None = None
    page_end: int | None = None
    token_count: int | None = None
    embedding: list[float] | None = None


class ChunkRepository:
    """Persistence operations for document chunks and embeddings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_many(
        self,
        document_id: uuid.UUID,
        chunks: list[ChunkInput],
    ) -> list[DocumentChunk]:
        records = [
            DocumentChunk(
                document_id=document_id,
                ordinal=chunk.ordinal,
                content=chunk.content,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                token_count=chunk.token_count,
                embedding=chunk.embedding,
            )
            for chunk in chunks
        ]
        self.session.add_all(records)
        self.session.flush()
        return records

    def list_for_document(
        self,
        document_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DocumentChunk]:
        _validate_pagination(limit, offset)
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.ordinal)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())


class ResearchQueryRepository:
    """Persistence operations for questions asked against a project."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, project_id: uuid.UUID, question: str) -> ResearchQuery:
        query = ResearchQuery(project_id=project_id, question=question)
        self.session.add(query)
        self.session.flush()
        return query

    def get(self, query_id: uuid.UUID) -> ResearchQuery | None:
        return self.session.get(ResearchQuery, query_id)

    def list_for_project(
        self,
        project_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ResearchQuery]:
        _validate_pagination(limit, offset)
        statement = (
            select(ResearchQuery)
            .where(ResearchQuery.project_id == project_id)
            .order_by(ResearchQuery.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
