from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[4]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MATCHES_FILE = PROCESSED_DIR / "matches.json"


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def load_processed_matches() -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    if not MATCHES_FILE.exists():
        return [], None

    payload = json.loads(MATCHES_FILE.read_text(encoding="utf-8"))
    matches = payload.get("matches", [])
    metadata = payload.get("metadata", {})

    normalized = []
    for match in matches:
        normalized.append(
            {
                **match,
                "tournament_year": match.get("tournament_year", 2026),
                "stage": match.get("stage", "Group stage"),
                "kickoff_at": parse_datetime(match["kickoff_at"]),
            }
        )
    return normalized, metadata


def write_processed_matches(payload: dict[str, Any], path: Path = MATCHES_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def apply_processed_data(data: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    processed_matches, metadata = load_processed_matches()
    if not processed_matches:
        return data

    merged = deepcopy(data)
    seed_matches = {match["id"]: match for match in merged["matches"]}
    for match in processed_matches:
        original = seed_matches.get(match["id"], {})
        seed_matches[match["id"]] = {**original, **match}

    merged["matches"] = sorted(seed_matches.values(), key=lambda match: match["kickoff_at"])
    merged["data_metadata"] = [
        {
            "collection": "matches",
            "mode": "processed",
            **(metadata or {}),
        }
    ]
    return merged


def processed_status() -> dict[str, Any]:
    matches, metadata = load_processed_matches()
    if not matches:
        return {
            "mode": "seeded",
            "collections": {},
            "metadata": None,
        }

    finished = sum(1 for match in matches if match.get("status") == "finished")
    return {
        "mode": "processed",
        "collections": {
            "matches": len(matches),
            "finished_matches": finished,
        },
        "metadata": metadata,
    }
