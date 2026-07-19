import pytest

from research_map.ingestion.extraction import ExtractedDocument, ExtractedPage
from research_map.ingestion.validation import (
    DocumentValidationError,
    validate_extracted_document,
    validate_size,
)


def test_validate_extracted_document_rejects_scanned_pdf() -> None:
    document = ExtractedDocument(
        metadata={},
        pages=[
            ExtractedPage(
                page_number=1,
                text="",
                word_count=0,
                width=400,
                height=600,
                rotation=0,
            )
        ],
    )

    with pytest.raises(DocumentValidationError, match="searchable text"):
        validate_extracted_document(document)


def test_validate_size_rejects_oversized_document() -> None:
    with pytest.raises(DocumentValidationError, match="exceeds the 1 MB limit"):
        validate_size(2 * 1024 * 1024, 1)
