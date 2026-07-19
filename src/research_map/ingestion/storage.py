from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from research_map.core.config import Settings
from research_map.ingestion.validation import (
    DocumentValidationError,
    validate_filename,
    validate_pdf_signature,
    validate_size,
)

CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True, slots=True)
class StoredUpload:
    path: Path
    content_hash: str
    size_bytes: int
    created: bool


async def store_pdf(
    file: UploadFile,
    project_id: UUID,
    settings: Settings,
) -> StoredUpload:
    """Stream a PDF to disk while calculating its content hash."""

    filename = (file.filename or "").strip()
    validate_filename(filename)

    destination_dir = settings.upload_dir / str(project_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_dir / f".{uuid4().hex}.part"
    digest = sha256()
    size_bytes = 0
    first_chunk = True

    try:
        with temporary_path.open("wb") as output:
            while chunk := await file.read(CHUNK_SIZE):
                if first_chunk:
                    validate_pdf_signature(chunk)
                first_chunk = False
                size_bytes += len(chunk)
                validate_size(size_bytes, settings.max_upload_size_mb)
                digest.update(chunk)
                output.write(chunk)

        if first_chunk:
            raise DocumentValidationError("The uploaded PDF is empty")

        content_hash = digest.hexdigest()
        destination_path = destination_dir / f"{content_hash}.pdf"
        if destination_path.exists():
            temporary_path.unlink(missing_ok=True)
            return StoredUpload(
                path=destination_path,
                content_hash=content_hash,
                size_bytes=size_bytes,
                created=False,
            )

        temporary_path.replace(destination_path)
        return StoredUpload(
            path=destination_path,
            content_hash=content_hash,
            size_bytes=size_bytes,
            created=True,
        )
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
