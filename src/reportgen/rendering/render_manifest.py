"""Records every numeric value resolved during rendering for audit.

Each entry pairs a (slide_id, block_key, source_key) coordinate with the
resolved display value. The manifest is written to `intermediates/render_manifest.json`
and is the contract that proves no number on the page was AI-authored.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class RenderRecord:
    slide_id: str
    block_key: str
    source_key: str
    resolved_value: str
    kind: str  # one of: metric, table_cell, chart_series, chart_category


@dataclass
class RenderManifest:
    records: list[RenderRecord] = field(default_factory=list)

    def add(self, *, slide_id: str, block_key: str, source_key: str, resolved_value: str, kind: str) -> None:
        self.records.append(
            RenderRecord(
                slide_id=slide_id,
                block_key=block_key,
                source_key=source_key,
                resolved_value=resolved_value,
                kind=kind,
            )
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps({"records": [asdict(r) for r in self.records]}, indent=indent)

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path
