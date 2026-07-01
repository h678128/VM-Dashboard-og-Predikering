from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.services.processed_data import load_processed_matches, write_processed_matches

FINISHED_STATUSES = {"FINISHED", "finished", "FT", "AET", "PEN", "full_time"}
LIVE_STATUSES = {
    "LIVE", "IN_PLAY", "PAUSED", "live", "in_play", "paused",
    "1H", "HT", "2H", "ET", "BT", "P",
}

TEAM_ALIASES = {
    "bosnia & herzegovina": "bosnia and herzegovina",
    "bosnia-herzegovina": "bosnia and herzegovina",
    "cote d'ivoire": "ivory coast",
    "cote divoire": "ivory coast",
    "congo dr": "dr congo",
    "congo democratic republic": "dr congo",
    "cape verde islands": "cape verde",
    "iran": "ir iran",
    "south korea": "korea republic",
    "usa": "united states",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_status(value: str | None, home_score: int | None, away_score: int | None) -> str:
    if value in FINISHED_STATUSES:
        return "finished"
    if value in LIVE_STATUSES:
        return "live"
    if home_score is not None and away_score is not None:
        return "finished"
    return "scheduled"


def normalize_group(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    group_match = re.search(r"group(?: stage)?[ _-]+([A-L])(?:\b|_)", text, re.IGNORECASE)
    if group_match:
        return group_match.group(1).upper()
    return text.upper() if re.fullmatch(r"[A-L]", text, re.IGNORECASE) else None


def normalized_team_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    key = " ".join(text.lower().replace(".", "").split())
    return TEAM_ALIASES.get(key, key)


def team_lookup(teams: list[dict[str, Any]]) -> dict[str, int]:
    lookup: dict[str, int] = {}
    for team in teams:
        lookup[str(team["id"])] = team["id"]
        lookup[normalized_team_key(team["name"])] = team["id"]
        lookup[normalized_team_key(team["fifa_code"])] = team["id"]
    return lookup


def find_team_id(value: Any, lookup: dict[str, int]) -> int | None:
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("id", "tla", "code", "fifa_code", "name", "shortName"):
            found = find_team_id(value.get(key), lookup)
            if found is not None:
                return found
        return None
    return lookup.get(normalized_team_key(value))


def score_from_row(row: dict[str, Any]) -> tuple[int | None, int | None]:
    if "home_score" in row or "away_score" in row:
        return row.get("home_score"), row.get("away_score")

    score = row.get("score")
    if not isinstance(score, dict):
        return None, None

    full_time = score.get("fullTime") or score.get("full_time") or score.get("ft") or {}
    if isinstance(full_time, dict):
        return full_time.get("home"), full_time.get("away")
    if isinstance(full_time, list) and len(full_time) >= 2:
        return full_time[0], full_time[1]
    return None, None


def penalty_score_from_row(row: dict[str, Any]) -> tuple[int | None, int | None]:
    score = row.get("score")
    if not isinstance(score, dict):
        return None, None
    penalties = score.get("penalties") or score.get("p")
    if isinstance(penalties, dict):
        return penalties.get("home"), penalties.get("away")
    if isinstance(penalties, list) and len(penalties) >= 2:
        return penalties[0], penalties[1]
    return None, None


def kickoff_from_row(row: dict[str, Any]) -> str:
    value = row.get("kickoff_at") or row.get("utcDate")
    if value:
        return str(value).replace("Z", "+00:00")

    date_value = row.get("date")
    time_value = row.get("time")
    if date_value and time_value:
        match = re.fullmatch(r"(\d{1,2}):(\d{2}) UTC([+-]\d{1,2})", str(time_value).strip())
        if not match:
            raise ValueError(f"Ukjent tidsformat: {time_value}")
        hour, minute, offset = (int(part) for part in match.groups())
        local_time = datetime.fromisoformat(str(date_value)).replace(
            hour=hour,
            minute=minute,
            tzinfo=timezone(timedelta(hours=offset)),
        )
        return local_time.astimezone(timezone.utc).isoformat()

    if not date_value:
        raise ValueError("Kamp mangler kickoff_at/utcDate/date.")
    return f"{date_value}T00:00:00+00:00"


def match_key(match: dict[str, Any]) -> tuple[int | None, int | None, str | None]:
    return (match.get("home_team_id"), match.get("away_team_id"), match.get("group_name"))


def seed_match_index(seed_matches: list[dict[str, Any]]) -> dict[tuple[int | None, int | None, str | None], dict[str, Any]]:
    return {match_key(match): match for match in seed_matches}


def api_football_rows(payload: dict[str, Any]) -> list[dict[str, Any]] | None:
    response = payload.get("response")
    if not isinstance(response, list):
        return None

    rows = []
    for item in response:
        if not isinstance(item, dict):
            continue
        fixture = item.get("fixture") or {}
        league = item.get("league") or {}
        venue = fixture.get("venue") or {}
        status = fixture.get("status") or {}
        teams = item.get("teams") or {}
        rows.append(
            {
                "id": fixture.get("id"),
                "home_team": teams.get("home"),
                "away_team": teams.get("away"),
                "kickoff_at": fixture.get("date"),
                "stadium": venue.get("name"),
                "city": venue.get("city"),
                "status": status.get("short") or status.get("long"),
                "home_score": (item.get("goals") or {}).get("home"),
                "away_score": (item.get("goals") or {}).get("away"),
                "group": league.get("round"),
                "stage": league.get("round"),
            }
        )
    return rows


def normalize_match_row(
    row: dict[str, Any],
    teams: list[dict[str, Any]],
    seed_matches: list[dict[str, Any]],
) -> dict[str, Any]:
    lookup = team_lookup(teams)
    home_value = row.get("homeTeam") or row.get("home_team") or row.get("team1")
    away_value = row.get("awayTeam") or row.get("away_team") or row.get("team2")
    home_team_id = row.get("home_team_id") or find_team_id(home_value, lookup)
    away_team_id = row.get("away_team_id") or find_team_id(away_value, lookup)

    def participant_label(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        reference = re.fullmatch(r"([WL])(\d+)", value.strip(), flags=re.IGNORECASE)
        if not reference:
            return None
        prefix, match_number = reference.groups()
        return f"{'Vinner' if prefix.upper() == 'W' else 'Taper'} kamp {match_number}"

    home_team_label = participant_label(home_value) if home_team_id is None else None
    away_team_label = participant_label(away_value) if away_team_id is None else None
    if (home_team_id is None and home_team_label is None) or (
        away_team_id is None and away_team_label is None
    ):
        raise ValueError(f"Klarte ikke mappe lag for kamp: {row}")

    group_name = row.get("group_name") or normalize_group(row.get("group") or row.get("stage"))
    home_score, away_score = score_from_row(row)
    home_penalty_score, away_penalty_score = penalty_score_from_row(row)
    seed_by_key = seed_match_index(seed_matches)
    seed_match = seed_by_key.get((home_team_id, away_team_id, group_name)) or next(
        (
            match
            for match in seed_matches
            if match.get("home_team_id") == home_team_id
            and match.get("away_team_id") == away_team_id
        ),
        {},
    )
    group_name = group_name or seed_match.get("group_name")
    provider_stage = str(row.get("stage") or row.get("round") or "")
    stage = "Group stage" if group_name else provider_stage or "Ukjent fase"

    return {
        "id": int(seed_match.get("id") or row.get("id")),
        "match_number": int(row.get("match_number") or row.get("matchNumber") or row.get("num") or 0) or None,
        "tournament_year": int(row.get("tournament_year", 2026)),
        "stage": stage,
        "group_name": group_name,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "home_team_label": home_team_label,
        "away_team_label": away_team_label,
        "kickoff_at": kickoff_from_row(row),
        "stadium": row.get("stadium") or row.get("ground") or seed_match.get("stadium") or "Ukjent stadion",
        "city": row.get("city") or row.get("hostCity") or row.get("ground") or seed_match.get("city") or "Ukjent by",
        "status": normalize_status(row.get("status"), home_score, away_score),
        "home_score": home_score,
        "away_score": away_score,
        "home_penalty_score": home_penalty_score,
        "away_penalty_score": away_penalty_score,
    }


def normalize_match_payload(
    payload: dict[str, Any],
    teams: list[dict[str, Any]],
    seed_matches: list[dict[str, Any]],
    source_name: str,
    source_url: str,
    processed_at: str | None = None,
) -> dict[str, Any]:
    timestamp = processed_at or utc_now_iso()
    raw_matches = payload.get("matches")
    if not isinstance(raw_matches, list):
        raw_matches = api_football_rows(payload)
    if not isinstance(raw_matches, list):
        raise ValueError("Kilden må inneholde en matches-liste.")

    matches = []
    skipped_unresolved_matches = 0
    for index, row in enumerate(raw_matches, start=1):
        if not isinstance(row, dict):
            continue
        candidate = {"id": 10_000 + index, **row} if row.get("id") is None else row
        try:
            matches.append(normalize_match_row(candidate, teams, seed_matches))
        except ValueError:
            if row.get("group") or row.get("group_name"):
                raise
            skipped_unresolved_matches += 1
    matches.sort(key=lambda match: match["kickoff_at"])

    source_metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    is_live_data = bool(source_metadata.get("is_live_data")) or source_name.startswith(
        "API-Football"
    )
    return {
        "metadata": {
            "dataset": source_metadata.get("dataset", "openfootball_world_cup_2026"),
            "source_name": source_metadata.get("source_name", source_name),
            "source_url": source_metadata.get("source_url", source_url),
            "source_updated_at": source_metadata.get("source_updated_at") or timestamp,
            "processed_at": timestamp,
            "timezone": "Europe/Oslo",
            "is_live_data": is_live_data,
            "skipped_unresolved_matches": skipped_unresolved_matches,
            "unresolved_participants": sum(
                int(match.get("home_team_id") is None) + int(match.get("away_team_id") is None)
                for match in matches
            ),
            "notes": source_metadata.get(
                "notes",
                ["Kilde-merket leverandørimport med cache og fallback."]
                if is_live_data
                else [
                    "OpenFootball CC0-snapshot med komplett terminliste.",
                    "Resultater oppdateres periodisk og er ikke sekund-for-sekund live.",
                    "FIFA er autoritativ kilde ved eventuelle avvik.",
                ],
            ),
        },
        "matches": matches,
    }


def import_matches_payload(
    payload: dict[str, Any],
    teams: list[dict[str, Any]],
    seed_matches: list[dict[str, Any]],
    source_name: str,
    source_url: str,
    output_path: Path | None = None,
    preserve_existing: bool = False,
) -> Path:
    normalized = normalize_match_payload(payload, teams, seed_matches, source_name, source_url)
    if preserve_existing:
        existing, existing_metadata = load_processed_matches()
        merged = list(existing)

        def same_fixture(first: dict[str, Any], second: dict[str, Any]) -> bool:
            first_number = first.get("match_number")
            second_number = second.get("match_number")
            if first_number and second_number:
                return first_number == second_number
            same_teams = (
                first.get("home_team_id") is not None
                and first.get("away_team_id") is not None
                and first.get("home_team_id") == second.get("home_team_id")
                and first.get("away_team_id") == second.get("away_team_id")
                and first.get("stage") == second.get("stage")
            )
            same_slot = (
                first.get("stage") == second.get("stage")
                and str(first.get("kickoff_at")).replace(" ", "T")[:16]
                == str(second.get("kickoff_at")).replace(" ", "T")[:16]
            )
            return same_teams or same_slot

        for update in normalized["matches"]:
            existing_index = next(
                (index for index, match in enumerate(merged) if same_fixture(match, update)),
                None,
            )
            if existing_index is None:
                merged.append(update)
            else:
                previous = merged[existing_index]
                combined = {**previous, **update}
                combined["id"] = previous["id"]
                combined["match_number"] = update.get("match_number") or previous.get(
                    "match_number"
                )
                if previous.get("status") == "finished" and update.get("status") != "finished":
                    combined.update(
                        {
                            "status": "finished",
                            "home_score": previous.get("home_score"),
                            "away_score": previous.get("away_score"),
                            "home_penalty_score": previous.get("home_penalty_score"),
                            "away_penalty_score": previous.get("away_penalty_score"),
                        }
                    )
                merged[existing_index] = combined

        normalized["matches"] = sorted(merged, key=lambda match: str(match["kickoff_at"]))
        normalized["metadata"]["notes"] = [
            "Leverandøroppdateringer er flettet inn i den komplette terminlisten.",
            "Uavklarte sluttspillplasser beholdes til deltakende lag er kjent.",
        ]
        if existing_metadata and existing_metadata.get("verification_sources"):
            normalized["metadata"]["verification_sources"] = existing_metadata[
                "verification_sources"
            ]
    return write_processed_matches(normalized, path=output_path) if output_path else write_processed_matches(normalized)
