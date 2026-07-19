from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from research_map.core.config import Settings

CHUNK_SIZE = 1024 * 1024
PDF_SIGNATURE = b"%PDF-"


class UploadValidationError(ValueError):
    """Raised when an uploaded file does not meet storage requirements."""


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
    if not filename:
        raise UploadValidationError("A filename is required")

    max_size = settings.max_upload_size_mb * 1024 * 1024
    if max_size <= 0:
        raise UploadValidationError("The upload size limit must be positive")

    destination_dir = settings.upload_dir / str(project_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_dir / f".{uuid4().hex}.part"
    digest = sha256()
    size_bytes = 0
    first_chunk = True

    try:
        with temporary_path.open("wb") as output:
            while chunk := await file.read(CHUNK_SIZE):
                if first_chunk and not chunk.startswith(PDF_SIGNATURE):
                    raise UploadValidationError("The uploaded file is not a PDF")
                first_chunk = False
                size_bytes += len(chunk)
                if size_bytes > max_size:
                    raise UploadValidationError(
                        f"The PDF exceeds the {settings.max_upload_size_mb} MB limit"
                    )
                digest.update(chunk)
                output.write(chunk)

        if first_chunk:
            raise UploadValidationError("The uploaded PDF is empty")

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
