import pymupdf
import pytest

from research_map.ingestion.extraction import PDFExtractionError, extract_pdf


def test_extract_pdf_preserves_page_text_and_metadata(tmp_path) -> None:
    pdf_path = tmp_path / "research-paper.pdf"
    document = pymupdf.open()
    first_page = document.new_page(width=400, height=600)
    first_page.insert_text((50, 80), "Research Map\nPage one")
    second_page = document.new_page()
    second_page.insert_text((50, 80), "Page two")
    document.set_metadata({"title": "Research Map paper", "author": "Test Author"})
    document.save(pdf_path)
    document.close()

    extracted = extract_pdf(pdf_path)

    assert extracted.page_count == 2
    assert extracted.metadata["title"] == "Research Map paper"
    assert extracted.pages[0].page_number == 1
    assert "Research Map" in extracted.pages[0].text
    assert extracted.pages[0].word_count == 4
    assert extracted.pages[0].width == 400
    assert extracted.pages[1].page_number == 2


def test_extract_pdf_rejects_invalid_file(tmp_path) -> None:
    pdf_path = tmp_path / "not-a-pdf.pdf"
    pdf_path.write_bytes(b"plain text")

    with pytest.raises(PDFExtractionError, match="Unable to extract PDF"):
        extract_pdf(pdf_path)
