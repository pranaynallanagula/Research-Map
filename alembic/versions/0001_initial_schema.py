"""Create the initial research schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    document_status = sa.Enum(
        "pending",
        "processing",
        "ready",
        "failed",
        name="document_status",
    )

    op.create_table(
        "research_projects",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_research_projects"),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_uri", sa.String(length=2048), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            document_status,
            server_default=sa.text("'pending'::document_status"),
            nullable=False,
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_documents_project_id_research_projects",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
        sa.UniqueConstraint(
            "project_id",
            "content_hash",
            name="uq_documents_project_content_hash",
        ),
    )

    op.create_table(
        "document_pages",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("document_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_document_pages_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document_pages"),
        sa.UniqueConstraint(
            "document_id",
            "page_number",
            name="uq_document_pages_document_page_number",
        ),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("document_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_document_chunks_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document_chunks"),
        sa.UniqueConstraint(
            "document_id",
            "ordinal",
            name="uq_document_chunks_document_ordinal",
        ),
    )

    op.create_table(
        "research_queries",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_research_queries_project_id_research_projects",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_research_queries"),
    )

    op.create_table(
        "research_answers",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("query_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=200), nullable=True),
        sa.Column("retrieved_chunk_count", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["query_id"],
            ["research_queries.id"],
            name="fk_research_answers_query_id_research_queries",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_research_answers"),
        sa.UniqueConstraint("query_id", name="uq_research_answers_query_id"),
    )

    op.create_table(
        "citations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("answer_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("chunk_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("citation_order", sa.Integer(), nullable=False),
        sa.Column("quoted_text", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["answer_id"],
            ["research_answers.id"],
            name="fk_citations_answer_id_research_answers",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["document_chunks.id"],
            name="fk_citations_chunk_id_document_chunks",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_citations"),
        sa.UniqueConstraint(
            "answer_id",
            "citation_order",
            name="uq_citations_answer_order",
        ),
    )

    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index(
        "ix_documents_project_status",
        "documents",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_document_pages_document_id",
        "document_pages",
        ["document_id"],
    )
    op.create_index(
        "ix_document_chunks_document_id",
        "document_chunks",
        ["document_id"],
    )
    op.create_index(
        "ix_document_chunks_document_page",
        "document_chunks",
        ["document_id", "page_start"],
    )
    op.create_index(
        "ix_research_queries_project_id",
        "research_queries",
        ["project_id"],
    )
    op.create_index("ix_citations_answer_id", "citations", ["answer_id"])
    op.create_index("ix_citations_chunk_id", "citations", ["chunk_id"])


def downgrade() -> None:
    op.drop_index("ix_citations_chunk_id", table_name="citations")
    op.drop_index("ix_citations_answer_id", table_name="citations")
    op.drop_table("citations")

    op.drop_table("research_answers")

    op.drop_index(
        "ix_research_queries_project_id",
        table_name="research_queries",
    )
    op.drop_table("research_queries")

    op.drop_index(
        "ix_document_chunks_document_page",
        table_name="document_chunks",
    )
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_document_pages_document_id", table_name="document_pages")
    op.drop_table("document_pages")

    op.drop_index("ix_documents_project_status", table_name="documents")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_project_id", table_name="documents")
    op.drop_table("documents")

    op.drop_table("research_projects")
    sa.Enum(name="document_status").drop(op.get_bind(), checkfirst=True)
