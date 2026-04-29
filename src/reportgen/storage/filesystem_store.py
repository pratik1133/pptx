from __future__ import annotations

import shutil
from pathlib import Path

from reportgen.storage.manifest import RunManifest, build_file_artifact


class FilesystemRunStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def ensure_structure(self) -> None:
        for name in ("inputs", "intermediates", "artifacts", "logs"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def copy_into(self, source: Path, relative_target: str) -> Path:
        target = self.root / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return target

    def write_text(self, relative_target: str, content: str) -> Path:
        target = self.root / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def add_artifact(self, manifest: RunManifest, label: str, path: Path) -> None:
        manifest.artifacts.append(build_file_artifact(label, path, self.root))

    def write_manifest(self, manifest: RunManifest) -> Path:
        target = self.root / "manifest.json"
        target.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        return target
