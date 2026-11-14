"""Privacy-conscious persisted diagnostic sessions."""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DiagnosticSession:
    source: str
    adapter_version: str
    results: List[Dict[str, Any]]
    created_at: str
    adapter: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        source: str,
        adapter_version: str,
        results: List[Dict[str, Any]],
        adapter: Optional[Dict[str, str]] = None,
    ) -> "DiagnosticSession":
        return cls(
            source,
            adapter_version,
            results,
            datetime.now(timezone.utc).isoformat(),
            adapter or {},
        )

    def save(self, destination: Path) -> None:
        """Write a JSON record. Callers must not include VINs or personal data."""
        destination.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n", encoding="utf-8")
