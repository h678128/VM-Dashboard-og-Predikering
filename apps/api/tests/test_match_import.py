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
