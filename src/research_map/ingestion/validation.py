from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from research_map.ingestion.extraction import ExtractedDocument


PDF_SIGNATURE = b"%PDF-"


class DocumentValidationError(ValueError):
    """Raised when a document cannot enter the processing pipeline."""


def validate_filename(filename: str) -> None:
    if not filename.strip():
        raise DocumentValidationError("A filename is required")


def validate_pdf_signature(first_chunk: bytes) -> None:
    if not first_chunk.startswith(PDF_SIGNATURE):
        raise DocumentValidationError("The uploaded file is not a PDF")


def validate_size(size_bytes: int, max_size_mb: int) -> None:
    if max_size_mb <= 0:
        raise DocumentValidationError("The upload size limit must be positive")
    if size_bytes > max_size_mb * 1024 * 1024:
        raise DocumentValidationError(f"The PDF exceeds the {max_size_mb} MB limit")


def validate_extracted_document(document: "ExtractedDocument") -> None:
    if document.page_count == 0:
        raise DocumentValidationError("The PDF does not contain any pages")
    if not any(page.text.strip() for page in document.pages):
        raise DocumentValidationError("The PDF contains no searchable text")
