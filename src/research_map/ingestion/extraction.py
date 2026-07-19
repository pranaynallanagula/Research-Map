from dataclasses import dataclass
from pathlib import Path

import pymupdf

from research_map.ingestion.validation import validate_extracted_document


class PDFExtractionError(ValueError):
    """Raised when a PDF cannot be opened or read."""


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    page_number: int
    text: str
    word_count: int
    width: float
    height: float
    rotation: int


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    metadata: dict[str, str | None]
    pages: list[ExtractedPage]

    @property
    def page_count(self) -> int:
        return len(self.pages)


def extract_pdf(path: Path) -> ExtractedDocument:
    """Extract searchable text and page metadata from a PDF file."""

    if not path.is_file():
        raise FileNotFoundError(path)

    try:
        with pymupdf.open(path) as document:  # type: ignore[no-untyped-call]
            metadata = {
                key: value
                for key, value in (document.metadata or {}).items()
                if key and (value is None or isinstance(value, str))
            }
            pages = [
                _extract_page(page, page_index)
                for page_index, page in enumerate(document)
            ]
    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise PDFExtractionError(f"Unable to extract PDF: {path.name}") from exc

    extracted_document = ExtractedDocument(metadata=metadata, pages=pages)
    validate_extracted_document(extracted_document)
    return extracted_document


def _extract_page(page: pymupdf.Page, page_index: int) -> ExtractedPage:
    text = page.get_text("text", sort=True).strip()  # type: ignore[no-untyped-call]
    rectangle = page.rect
    return ExtractedPage(
        page_number=page_index + 1,
        text=text,
        word_count=len(text.split()),
        width=rectangle.width,
        height=rectangle.height,
        rotation=page.rotation,
    )
