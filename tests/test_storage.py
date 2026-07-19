import asyncio
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import UploadFile

from research_map.core.config import Settings
from research_map.ingestion.storage import store_pdf
from research_map.ingestion.validation import DocumentValidationError


def test_store_pdf_hashes_and_deduplicates(tmp_path) -> None:
    settings = Settings(_env_file=None, upload_dir=tmp_path)
    project_id = uuid4()
    pdf_content = b"%PDF-1.7\nresearch content"

    first = asyncio.run(
        store_pdf(
            UploadFile(BytesIO(pdf_content), filename="paper.pdf"),
            project_id,
            settings,
        )
    )
    second = asyncio.run(
        store_pdf(
            UploadFile(BytesIO(pdf_content), filename="copy.pdf"),
            project_id,
            settings,
        )
    )

    assert first.created is True
    assert second.created is False
    assert first.path == second.path
    assert first.path.exists()


def test_store_pdf_rejects_non_pdf(tmp_path) -> None:
    settings = Settings(_env_file=None, upload_dir=tmp_path)
    upload = UploadFile(BytesIO(b"plain text"), filename="notes.txt")

    with pytest.raises(DocumentValidationError, match="not a PDF"):
        asyncio.run(store_pdf(upload, uuid4(), settings))
