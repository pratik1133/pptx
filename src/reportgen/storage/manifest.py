from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class FileArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    path: str
    sha256: str
    size_bytes: int = Field(ge=0)


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    created_at: datetime
    company_ticker: str
    status: str
    artifacts: list[FileArtifact] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_file_artifact(label: str, path: Path, root: Path) -> FileArtifact:
    return FileArtifact(
        label=label,
        path=str(path.relative_to(root)),
        sha256=hash_file(path),
        size_bytes=path.stat().st_size,
    )


def new_manifest(run_id: str, company_ticker: str, status: str) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        created_at=datetime.now(timezone.utc),
        company_ticker=company_ticker,
        status=status,
    )
