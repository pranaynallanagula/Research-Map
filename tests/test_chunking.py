import pytest

from research_map.ingestion.chunking import ChunkingConfig, chunk_pages
from research_map.ingestion.cleaning import CleanedPage, clean_text


def test_clean_text_preserves_paragraphs_and_joins_hyphenated_lines() -> None:
    text = "First para-\ngraph.\r\n\r\nSecond   paragraph."

    assert clean_text(text) == "First paragraph.\n\nSecond paragraph."


def test_chunk_pages_preserves_page_boundaries_and_overlap() -> None:
    pages = [
        CleanedPage(
            page_number=3,
            text="one two three four five six seven",
            word_count=7,
            width=400,
            height=600,
            rotation=0,
        )
    ]

    chunks = chunk_pages(
        pages,
        ChunkingConfig(max_words=4, overlap_words=1),
    )

    assert [chunk.ordinal for chunk in chunks] == [0, 1]
    assert chunks[0].content == "one two three four"
    assert chunks[1].content == "four five six seven"
    assert chunks[0].page_start == chunks[1].page_start == 3


def test_chunking_config_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="smaller than max_words"):
        ChunkingConfig(max_words=10, overlap_words=10)
