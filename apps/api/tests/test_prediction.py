from zoneinfo import ZoneInfo

from app.services.live_probability import probability_events, update_live_probability
from app.services.prediction import predict_match, score_prediction
from app.services.seed_data import seed
from app.services.standings import calculate_group_standings
from app.api.routes import (
    create_prediction,
    data_status,
    list_predictions,
    live_probability,
    match_events,
    matches as route_matches,
    model_lab,
    model_prediction,
    match_lineups,
    top_scorer_prediction,
    top_scorers,
    USER_PREDICTIONS,
)
from app.schemas import PredictionIn


def test_prediction_is_deterministic_and_sums_to_one():
    data = seed()
    norway = data["teams"][0]
    senegal = data["teams"][2]
    first = predict_match(norway, senegal, data["teams"], match_id=1)
    second = predict_match(norway, senegal, data["teams"], match_id=1)

    total = (
        first["home_win_probability"]
        + first["draw_probability"]
        + first["away_win_probability"]
    )
    assert first["home_win_probability"] == second["home_win_probability"]
    assert abs(total - 1.0) < 0.001


def test_prediction_points_are_additive():
    prediction = {
        "predicted_home_score": 2,
        "predicted_away_score": 1,
        "predicted_winner_team_id": 10,
        "first_goalscorer_player_id": 99,
        "tournament_top_scorer_player_id": 42,
    }
    actual = {
        "home_score": 2,
        "away_score": 1,
        "home_team_id": 10,
        "away_team_id": 11,
        "first_goalscorer_player_id": 99,
        "tournament_top_scorer_player_id": 42,
    }

    result = score_prediction(prediction, actual)

    assert result["total_points"] == 24
    assert result["breakdown"]["correct_winner"] == 3
    assert result["breakdown"]["correct_goal_difference"] == 2
    assert result["breakdown"]["exact_score"] == 5
    assert result["breakdown"]["correct_first_goalscorer"] == 4
    assert result["breakdown"]["correct_tournament_top_scorer"] == 10


def test_live_probability_explains_significant_change():
    prematch = {
        "home_win_probability": 0.47,
        "draw_probability": 0.27,
        "away_win_probability": 0.26,
    }
    snapshots = [
        {
            "id": 1,
            "match_id": 99,
            "minute": 0,
            "home_score": 0,
            "away_score": 0,
            "home_xg": 0.0,
            "away_xg": 0.0,
            "home_shots_on_target": 0,
            "away_shots_on_target": 0,
            "home_dangerous_attacks": 0,
            "away_dangerous_attacks": 0,
            "home_red_cards": 0,
            "away_red_cards": 0,
            "home_yellow_cards": 0,
            "away_yellow_cards": 0,
            "home_win_probability": 0.47,
        },
        {
            "id": 2,
            "match_id": 99,
            "minute": 24,
            "home_score": 1,
            "away_score": 0,
            "home_xg": 0.74,
            "away_xg": 0.15,
            "home_shots_on_target": 3,
            "away_shots_on_target": 0,
            "home_dangerous_attacks": 18,
            "away_dangerous_attacks": 7,
            "home_red_cards": 0,
            "away_red_cards": 0,
            "home_yellow_cards": 0,
            "away_yellow_cards": 0,
            "home_win_probability": 0.68,
        },
    ]
    current = update_live_probability(prematch, snapshots[1])
    events = probability_events(99, snapshots)

    assert current["home_win_probability"] > prematch["home_win_probability"]
    assert events
    assert events[0]["event_type"] == "goal"


def test_seed_schedule_uses_verified_group_results_only():
    data = seed()
    matches = data["matches"]

    assert matches
    assert len(data["teams"]) == 48
    assert {team["group_name"] for team in data["teams"]} == set("ABCDEFGHIJKL")
    assert {match["group_name"] for match in matches} == {"I", "J", "K", "L"}
    assert all(match["stage"] == "Group stage" for match in matches)
    finished = [
        (match["group_name"], match["home_team_id"], match["away_team_id"], match["home_score"], match["away_score"])
        for match in matches
        if match["status"] == "finished"
    ]
    assert ("I", 1, 3, 3, 2) in finished
    assert ("I", 2, 4, 3, 0) in finished
    assert ("K", 9, 11, 5, 0) in finished
    assert ("L", 13, 15, 0, 0) in finished
    assert all(
        match["home_score"] is None and match["away_score"] is None
        for match in matches
        if match["status"] == "scheduled"
    )


def test_match_schedule_is_sorted_and_uses_correct_oslo_time():
    ordered = route_matches()
    norway_senegal = next(
        match for match in ordered if match["home_team"]["name"] == "Norway" and match["away_team"]["name"] == "Senegal"
    )
    oslo_time = norway_senegal["kickoff_at"].astimezone(ZoneInfo("Europe/Oslo"))

    assert ordered == sorted(ordered, key=lambda match: match["kickoff_at"])
    assert oslo_time.strftime("%Y-%m-%d %H:%M") == "2026-06-23 02:00"


def test_data_status_exposes_counts_and_prediction_flow():
    USER_PREDICTIONS.clear()

    status = data_status()
    assert status["timezone"] == "Europe/Oslo"
    assert status["mode"] == "processed"
    assert status["source"] == "SB Nation World Cup schedule and scores"
    assert status["source_url"].startswith("https://")
    assert status["last_updated"]
    assert status["is_live_data"] is False
    assert status["counts"]["teams"] == len(seed()["teams"])

    created = create_prediction(
        PredictionIn(
            match_id=1,
            predicted_home_score=1,
            predicted_away_score=0,
            predicted_winner_team_id=1,
            first_goalscorer_player_id=1,
            tournament_winner_team_id=2,
            tournament_top_scorer_player_id=3,
        )
    )

    assert created["points"] > 0
    assert list_predictions(limit=5)[-1]["id"] == created["id"]


def test_players_separate_international_and_tournament_goals():
    mbappe = next(item for item in seed()["players"] if item["name"] == "Kylian Mbappe")
    haaland = next(item for item in seed()["players"] if item["name"] == "Erling Haaland")

    assert mbappe["goals"] == 52
    assert mbappe["tournament_goals"] == 2
    assert haaland["goals"] == 38
    assert haaland["tournament_goals"] == 2


def test_model_lab_exposes_selectable_model_levels():
    lab = model_lab()

    assert lab["active_model_id"] == "country"
    assert [model["id"] for model in lab["models"]] == ["simple", "country", "advanced", "expert"]
    assert [forecast["model_id"] for forecast in lab["model_forecasts"]] == ["simple", "country", "advanced", "expert"]
    assert all(model["status"] == "available" for model in lab["models"])
    assert lab["models"][-1]["name"] == "Ekspertmodell"
    assert lab["models"][-1]["features"]
    assert all(forecast["match_winner_team"]["name"] for forecast in lab["model_forecasts"])
    assert all(forecast["cup_winner_team"]["name"] for forecast in lab["model_forecasts"])
    assert lab["training_plan"]


def test_match_prediction_can_select_different_models():
    simple = model_prediction(3, model_id="simple")
    expert = model_prediction(3, model_id="expert")

    assert simple["model_id"] == "simple"
    assert expert["model_id"] == "expert"
    assert expert["model_version"] == "wc-v0.4-many-parameters"
    assert len(expert["explanation_json"]["features_used"]) > len(simple["explanation_json"]["features_used"])
    assert simple["home_win_probability"] != expert["home_win_probability"]


def test_live_top_scorers_only_use_registered_goal_events():
    standings = top_scorers()

    assert [(item["player"]["name"], item["goals"]) for item in standings] == [
        ("Lionel Messi", 3),
        ("Harry Kane", 2),
        ("Erling Haaland", 2),
        ("Kylian Mbappe", 2),
        ("Joao Neves", 1),
        ("Romano Schmid", 1),
        ("Martin Baturina", 1),
        ("Ali Olwan", 1),
        ("Aymen Hussein", 1),
        ("Petar Musa", 1),
        ("Yoane Wissa", 1),
        ("Jude Bellingham", 1),
        ("Leo Ostigard", 1),
        ("Bradley Barcola", 1),
        ("Marcus Rashford", 1),
        ("Marko Arnautovic", 1),
    ]


def test_group_standings_are_calculated_from_finished_matches():
    data = seed()
    groups = calculate_group_standings(data["teams"], data["matches"])
    group_names = [group["group_name"] for group in groups]
    group_a = next(group for group in groups if group["group_name"] == "A")
    group_i = next(group for group in groups if group["group_name"] == "I")
    group_k = next(group for group in groups if group["group_name"] == "K")

    assert group_names == list("ABCDEFGHIJKL")
    assert [row["team"]["name"] for row in group_a["standings"]] == [
        "Mexico",
        "South Korea",
        "Czech Republic",
        "South Africa",
    ]
    assert all(row["played"] == 0 for row in group_a["standings"])
    assert [
        (row["team"]["name"], row["points"], row["goal_difference"])
        for row in group_i["standings"]
    ] == [
        ("France", 6, 5),
        ("Norway", 6, 4),
        ("Senegal", 0, -3),
        ("Iraq", 0, -6),
    ]
    assert [(row["team"]["name"], row["points"]) for row in group_k["standings"][:2]] == [
        ("Colombia", 6),
        ("Portugal", 4),
    ]


def test_top_scorer_prediction_returns_model_forecast():
    forecast = top_scorer_prediction()

    assert forecast
    assert forecast[0]["probability"] >= forecast[-1]["probability"]
    assert forecast[0]["expected_goals"] > 0
    assert "spiller-rating" in forecast[0]["signals"]


def test_seed_matches_do_not_expose_fake_lineups():
    assert match_lineups(1) == []


def test_match_events_are_sorted_and_enriched():
    events = match_events(2)

    assert [event["minute"] for event in events] == [18, 39, 45, 72, 90]
    assert events[0]["event_type"] == "goal"
    assert events[0]["player"]["name"] == "Erling Haaland"
    assert events[0]["team"]["name"] == "Norway"
    assert events[-1]["player"] is None


def test_live_probability_marks_missing_possession_as_unavailable():
    payload = live_probability(3)

    assert payload["timeline"] == []
    assert payload["current"]["home_possession"] is None
    assert payload["current"]["away_possession"] is None

