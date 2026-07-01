import json

from app.services.match_import import import_matches_payload, normalize_match_payload
from app.services.seed_data import MATCHES, TEAMS


def test_normalize_processed_match_snapshot():
    payload = {
        "metadata": {
            "source_name": "Testkilde",
            "source_url": "https://example.test/matches.json",
            "is_live_data": False,
        },
        "matches": [
            {
                "id": 3,
                "group_name": "I",
                "home_team_id": 1,
                "away_team_id": 3,
                "kickoff_at": "2026-06-23T00:00:00+00:00",
                "stadium": "New York New Jersey Stadium",
                "city": "New York/New Jersey",
                "status": "finished",
                "home_score": 3,
                "away_score": 2,
            }
        ],
    }

    normalized = normalize_match_payload(
        payload,
        TEAMS,
        MATCHES,
        source_name="Fallback-navn",
        source_url="https://fallback.test",
        processed_at="2026-06-25T18:00:00+00:00",
    )

    assert normalized["metadata"]["source_name"] == "Testkilde"
    assert normalized["metadata"]["processed_at"] == "2026-06-25T18:00:00+00:00"
    assert normalized["matches"][0]["id"] == 3
    assert normalized["matches"][0]["status"] == "finished"


def test_normalize_football_data_style_payload():
    payload = {
        "matches": [
            {
                "id": 9001,
                "utcDate": "2026-06-23T00:00:00Z",
                "status": "FINISHED",
                "stage": "GROUP_I",
                "group": "GROUP_I",
                "homeTeam": {"tla": "NOR", "name": "Norway"},
                "awayTeam": {"tla": "SEN", "name": "Senegal"},
                "score": {"fullTime": {"home": 3, "away": 2}},
            }
        ]
    }

    normalized = normalize_match_payload(
        payload,
        TEAMS,
        MATCHES,
        source_name="football-data.org",
        source_url="https://api.football-data.org/v4/competitions/WC/matches",
        processed_at="2026-06-25T18:00:00+00:00",
    )
    match = normalized["matches"][0]

    assert match["id"] == 3
    assert match["group_name"] == "I"
    assert match["home_team_id"] == 1
    assert match["away_team_id"] == 3
    assert match["home_score"] == 3
    assert match["away_score"] == 2


def test_import_matches_payload_writes_processed_json(tmp_path):
    output_path = tmp_path / "matches.json"
    payload = {
        "matches": [
            {
                "id": 4,
                "group_name": "I",
                "home_team_id": 2,
                "away_team_id": 4,
                "kickoff_at": "2026-06-22T21:00:00+00:00",
                "status": "finished",
                "home_score": 3,
                "away_score": 0,
            }
        ]
    }

    written = import_matches_payload(
        payload,
        TEAMS,
        MATCHES,
        source_name="Test",
        source_url="file://test",
        output_path=output_path,
    )
    saved = json.loads(written.read_text(encoding="utf-8"))

    assert written == output_path
    assert saved["metadata"]["source_name"] == "Test"
    assert saved["matches"][0]["id"] == 4
    assert saved["matches"][0]["stadium"] == "Philadelphia Stadium"


def test_live_import_preserves_unresolved_schedule_slots(tmp_path):
    output_path = tmp_path / "matches.json"
    payload = {
        "matches": [
            {
                "id": 3,
                "group_name": "I",
                "home_team_id": 1,
                "away_team_id": 3,
                "kickoff_at": "2026-06-23T00:00:00+00:00",
                "status": "finished",
                "home_score": 3,
                "away_score": 2,
            },
            {
                "id": 10078,
                "stage": "Round of 32",
                "home_team_id": 35,
                "away_team_id": 1,
                "kickoff_at": "2026-06-30T17:00:00+00:00",
                "status": "scheduled",
            },
        ]
    }

    written = import_matches_payload(
        payload,
        TEAMS,
        MATCHES,
        source_name="Liveleverandør",
        source_url="https://example.test/live",
        output_path=output_path,
        preserve_existing=True,
    )
    saved = json.loads(written.read_text(encoding="utf-8"))

    assert len(saved["matches"]) == 104
    assert any(match.get("match_number") == 104 for match in saved["matches"])
    verified = next(match for match in saved["matches"] if match.get("match_number") == 78)
    assert verified["group_name"] is None
    assert verified["status"] == "finished"
    assert (verified["home_score"], verified["away_score"]) == (1, 2)
    assert saved["metadata"]["verification_sources"][0]["match_number"] == 78
    assert "komplette terminlisten" in saved["metadata"]["notes"][0]


def test_normalize_api_football_fixture_payload():
    payload = {
        "response": [
            {
                "fixture": {
                    "id": 120026,
                    "date": "2026-06-22T21:00:00+00:00",
                    "status": {"short": "FT"},
                    "venue": {"name": "Philadelphia Stadium", "city": "Philadelphia"},
                },
                "league": {"round": "Group I - 2"},
                "teams": {"home": {"name": "France"}, "away": {"name": "Iraq"}},
                "goals": {"home": 3, "away": 0},
            }
        ]
    }

    normalized = normalize_match_payload(
        payload,
        TEAMS,
        MATCHES,
        source_name="API-Football kamper",
        source_url="https://v3.football.api-sports.io/fixtures",
        processed_at="2026-06-23T00:00:00+00:00",
    )
    match = normalized["matches"][0]

    assert normalized["metadata"]["is_live_data"] is True
    assert normalized["metadata"]["source_updated_at"] == "2026-06-23T00:00:00+00:00"
    assert match["id"] == 4
    assert match["group_name"] == "I"
    assert match["status"] == "finished"
    assert match["home_score"] == 3
    assert match["away_score"] == 0


def test_normalize_openfootball_snapshot_and_keep_unresolved_knockout_slots():
    payload = {
        "matches": [
            {
                "round": "Matchday 1",
                "date": "2026-06-11",
                "time": "13:00 UTC-6",
                "team1": "Mexico",
                "team2": "South Africa",
                "score": {"ft": [2, 0]},
                "group": "Group A",
                "ground": "Mexico City",
            },
            {
                "round": "Round of 32",
                "num": 74,
                "date": "2026-06-29",
                "time": "16:30 UTC-4",
                "team1": "Germany",
                "team2": "Paraguay",
                "score": {"ft": [1, 1], "p": [3, 4]},
                "ground": "Boston",
            },
            {
                "round": "Round of 16",
                "num": 89,
                "date": "2026-07-04",
                "time": "12:00 UTC-4",
                "team1": "W74",
                "team2": "W77",
                "ground": "Philadelphia",
            },
        ]
    }

    normalized = normalize_match_payload(
        payload,
        TEAMS,
        MATCHES,
        source_name="OpenFootball World Cup 2026 (CC0)",
        source_url="https://example.test/worldcup.json",
        processed_at="2026-06-30T12:00:00+00:00",
    )
    match = normalized["matches"][0]

    assert match["home_team_id"] == 17
    assert match["away_team_id"] == 18
    assert match["id"] == 10_001
    assert match["kickoff_at"] == "2026-06-11T19:00:00+00:00"
    assert match["home_score"] == 2
    assert match["status"] == "finished"
    knockout = normalized["matches"][1]
    assert knockout["match_number"] == 74
    assert knockout["home_penalty_score"] == 3
    assert knockout["away_penalty_score"] == 4
    unresolved = normalized["matches"][2]
    assert unresolved["match_number"] == 89
    assert unresolved["home_team_id"] is None
    assert unresolved["away_team_id"] is None
    assert unresolved["home_team_label"] == "Vinner kamp 74"
    assert unresolved["away_team_label"] == "Vinner kamp 77"
    assert unresolved["status"] == "scheduled"
    assert normalized["metadata"]["skipped_unresolved_matches"] == 0
    assert normalized["metadata"]["unresolved_participants"] == 2
    assert normalized["metadata"]["is_live_data"] is False
