from __future__ import annotations

from typing import Any

from app.services.external_data import configured_sources, fetch_json
from app.services.match_import import import_matches_payload
from app.services.seed_data import MATCHES, TEAMS


def refresh_schedule_data(force: bool = False) -> dict[str, Any]:
    source = next((item for item in configured_sources() if item.key == "fifa_schedule"), None)
    if source is None or not source.url:
        return {"status": "not_configured", "updated": []}

    result = fetch_json(source, force=force)
    payload = result.get("payload")
    if not payload:
        return {
            "status": result["status"],
            "message": result.get("message"),
            "updated": [],
        }

    path = import_matches_payload(
        payload,
        TEAMS,
        MATCHES,
        source_name=source.label,
        source_url=source.url,
        preserve_existing=True,
    )
    return {
        "status": "updated" if result["status"] == "fetched" else result["status"],
        "updated": [str(path)],
    }
