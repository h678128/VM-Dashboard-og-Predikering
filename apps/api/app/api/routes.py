from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.domain import UserPrediction as UserPredictionModel
from app.schemas import PredictionIn
from app.services.broadcasts import is_official_broadcast_link
from app.services.external_data import source_statuses
from app.services.historical import HISTORICAL_INSIGHTS
from app.services.live_probability import probability_events, update_live_probability
from app.services.prediction import (
    FEATURES,
    available_models,
    get_model_config,
    model_feature_importance,
    predict_match,
    team_strength,
)
from app.services.processed_data import load_processed_player_stats, processed_status
from app.services.rate_limit import enforce_rate_limit
from app.services.seed_data import find_one, seed
from app.services.simulation import simulate_match, simulate_tournament
from app.services.standings import calculate_group_standings

router = APIRouter()
USER_PREDICTIONS: list[dict] = []
PREDICTION_STORE_LIMIT = 500
DEFAULT_PUBLIC_PREDICTION_LIMIT = 25
MAX_PUBLIC_PREDICTION_LIMIT = 100
TEAM_NAMES_NO = {
    "Norway": "Norge",
    "France": "Frankrike",
    "Iraq": "Irak",
    "Netherlands": "Nederland",
    "Spain": "Spania",
    "Brazil": "Brasil",
}
STATUS_LABELS_NO = {"scheduled": "Ikke startet", "live": "Direkte", "finished": "Ferdig"}


def usable_db(db: object) -> Session | None:
    return db if hasattr(db, "add") and hasattr(db, "query") else None


def serialize_prediction(row: UserPredictionModel) -> dict:
    return {
        "id": row.id,
        "match_id": row.match_id,
        "user_name": row.user_name,
        "predicted_home_score": row.predicted_home_score,
        "predicted_away_score": row.predicted_away_score,
        "predicted_winner_team_id": row.predicted_winner_team_id,
        "first_goalscorer_player_id": row.first_goalscorer_player_id,
        "group_winners_json": row.group_winners_json,
        "tournament_winner_team_id": row.tournament_winner_team_id,
        "tournament_top_scorer_player_id": row.tournament_top_scorer_player_id,
        "points": row.points,
        "created_at": row.created_at,
        "scoring": row.scoring_json,
    }


def prediction_count(db: object) -> int:
    db_session = usable_db(db)
    if not db_session:
        return len(USER_PREDICTIONS)
    try:
        return db_session.query(UserPredictionModel).count()
    except SQLAlchemyError:
        db_session.rollback()
        return len(USER_PREDICTIONS)


def append_memory_prediction(prediction_dict: dict) -> dict:
    prediction_dict["id"] = len(USER_PREDICTIONS) + 1
    USER_PREDICTIONS.append(prediction_dict)
    if len(USER_PREDICTIONS) > PREDICTION_STORE_LIMIT:
        del USER_PREDICTIONS[: len(USER_PREDICTIONS) - PREDICTION_STORE_LIMIT]
    return prediction_dict


def utc_datetime(value: datetime | str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def validate_prediction_submission(
    prediction: PredictionIn,
    data: dict,
    now: datetime | None = None,
) -> dict:
    match_item = next(
        (item for item in data["matches"] if item["id"] == prediction.match_id),
        None,
    )
    if not match_item:
        raise HTTPException(404, "Kampen finnes ikke.")

    current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if match_item.get("status") != "scheduled" or utc_datetime(match_item["kickoff_at"]) <= current_time:
        raise HTTPException(409, "Tipsfristen for denne kampen er passert.")

    home_team_id = match_item["home_team_id"]
    away_team_id = match_item["away_team_id"]
    predicted_winner = prediction.predicted_winner_team_id
    valid_winners = {home_team_id, away_team_id, None}
    if predicted_winner not in valid_winners:
        raise HTTPException(422, "Vinneren må være et av lagene i kampen eller uavgjort.")

    if prediction.predicted_home_score > prediction.predicted_away_score:
        score_winner = home_team_id
    elif prediction.predicted_away_score > prediction.predicted_home_score:
        score_winner = away_team_id
    else:
        score_winner = None
    if predicted_winner != score_winner:
        raise HTTPException(422, "Valgt vinner må samsvare med det oppgitte resultatet.")

    teams_by_id = {team["id"]: team for team in data["teams"]}
    players_by_id = {player["id"]: player for player in data["players"]}
    first_scorer_id = prediction.first_goalscorer_player_id
    if first_scorer_id is not None:
        first_scorer = players_by_id.get(first_scorer_id)
        if not first_scorer or first_scorer["team_id"] not in {home_team_id, away_team_id}:
            raise HTTPException(422, "Første målscorer må tilhøre et av lagene i kampen.")
        if prediction.predicted_home_score + prediction.predicted_away_score == 0:
            raise HTTPException(422, "En målløs kamp kan ikke ha en første målscorer.")

    if (
        prediction.tournament_winner_team_id is not None
        and prediction.tournament_winner_team_id not in teams_by_id
    ):
        raise HTTPException(422, "Turneringsvinneren finnes ikke.")
    if (
        prediction.tournament_top_scorer_player_id is not None
        and prediction.tournament_top_scorer_player_id not in players_by_id
    ):
        raise HTTPException(422, "Turneringens toppscorer finnes ikke.")

    for group_name, team_id in (prediction.group_winners_json or {}).items():
        team = teams_by_id.get(team_id)
        if not team or team.get("group_name") != group_name:
            raise HTTPException(422, f"Gruppevinneren for gruppe {group_name} er ugyldig.")

    return match_item


def prediction_write_rate_limit(request: Request) -> None:
    enforce_rate_limit(
        request,
        "predictions:write",
        settings.prediction_rate_limit,
        settings.rate_limit_window_seconds,
    )


def simulation_rate_limit(request: Request) -> None:
    enforce_rate_limit(
        request,
        "simulation",
        settings.simulation_rate_limit,
        settings.rate_limit_window_seconds,
    )


def enrich_match(match: dict, data: dict) -> dict:
    return {
        **match,
        "kickoff_timezone": "Europe/Oslo",
        "home_team": next(team for team in data["teams"] if team["id"] == match["home_team_id"]),
        "away_team": next(team for team in data["teams"] if team["id"] == match["away_team_id"]),
    }


def ticker_match_label(match: dict, data: dict) -> str:
    home = next(team for team in data["teams"] if team["id"] == match["home_team_id"])
    away = next(team for team in data["teams"] if team["id"] == match["away_team_id"])
    score = (
        "ikke startet"
        if match["status"] == "scheduled"
        else f"{match.get('home_score') or 0}-{match.get('away_score') or 0}"
    )
    home_name = TEAM_NAMES_NO.get(home["name"], home["name"])
    away_name = TEAM_NAMES_NO.get(away["name"], away["name"])
    status = STATUS_LABELS_NO.get(match["status"], match["status"])
    return f"{home_name} - {away_name} · {score} · {status}"


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "timezone": "Europe/Oslo", "model_version": settings.model_version}


@router.get("/data/status")
def data_status(db: Session | None = Depends(get_db)) -> dict:
    data = seed()
    processed = processed_status()
    metadata = processed["metadata"] or {}
    sources = source_statuses()
    configured_sources = sum(1 for source in sources if source["configured"])
    cached_sources = sum(1 for source in sources if source["cached"])
    external_match_feed_configured = any(
        source["configured"] for source in sources if source["key"] != "world_bank"
    )
    return {
        "source": metadata.get("source_name", settings.live_data_provider),
        "source_url": metadata.get("source_url"),
        "mode": "processed"
        if processed["mode"] == "processed"
        else "external"
        if settings.live_data_provider != "seeded" or external_match_feed_configured
        else "seeded",
        "is_live_data": bool(metadata.get("is_live_data", False)),
        "last_updated": metadata.get("source_updated_at"),
        "processed_at": metadata.get("processed_at"),
        "timezone": "Europe/Oslo",
        "model_version": settings.model_version,
        "counts": {
            "teams": len(data["teams"]),
            "players": len(data["players"]),
            "matches": len(data["matches"]),
            "broadcasts": len(data["broadcasts"]),
            "live_snapshots": len(data["live_snapshots"]),
            "user_predictions": prediction_count(db),
        },
        "data_flow": [
            "API-et er primær datakilde for frontend.",
            f"Processed kampdata: {processed['collections'].get('matches', 0)} kamper, "
            f"{processed['collections'].get('finished_matches', 0)} ferdige.",
            f"{configured_sources} eksterne datakilder er konfigurert, {cached_sources} har raw-cache.",
            "Seed-data brukes som trygg fallback når liveleverandør ikke er koblet på.",
            "Brukerprediksjoner lagres ved innsending og poengsettes etter verifiserte resultater.",
        ],
    }


@router.get("/data/sources")
def data_sources() -> dict:
    return {
        "mode": settings.live_data_provider,
        "cache_ttl_seconds": settings.external_data_cache_ttl_seconds,
        "raw_storage": settings.external_data_cache_dir,
        "sources": source_statuses(),
    }


@router.get("/live/ticker")
def live_ticker() -> dict:
    data = seed()
    live_matches = [match for match in data["matches"] if match["status"] == "live"]
    sorted_matches = sorted(data["matches"], key=lambda match: match["kickoff_at"])
    featured = live_matches or sorted_matches[:5]
    items = [
        {
            "kind": "match",
            "label": ticker_match_label(match, data),
            "match_id": match["id"],
            "status": match["status"],
            "kickoff_at": match["kickoff_at"],
        }
        for match in featured
    ]
    items.extend(
        [
            {"kind": "meta", "label": "Alle tider vises i Europe/Oslo"},
            {
                "kind": "meta",
                "label": "Kun offisielle norske TV-lenker: NRK, NRK TV, TV 2 og TV 2 Play",
            },
            {
                "kind": "meta",
                "label": "Prediksjoner og modellforklaringer oppdateres når live-data er koblet på",
            },
        ]
    )
    return {
        "mode": "live" if live_matches else "scheduled",
        "timezone": "Europe/Oslo",
        "poll_interval_seconds": settings.live_poll_interval_seconds,
        "items": items,
    }


@router.get("/teams")
def teams() -> list[dict]:
    return seed()["teams"]


@router.get("/teams/{team_id}")
def team(team_id: int) -> dict:
    item = find_one("teams", team_id)
    if not item:
        raise HTTPException(404, "Team not found")
    players = [player for player in seed()["players"] if player["team_id"] == team_id]
    return item | {"players": players}


@router.get("/players")
def players() -> list[dict]:
    return seed()["players"]


@router.get("/players/{player_id}")
def player(player_id: int) -> dict:
    item = find_one("players", player_id)
    if not item:
        raise HTTPException(404, "Player not found")
    return item


@router.get("/matches")
def matches() -> list[dict]:
    data = seed()
    return [enrich_match(match, data) for match in sorted(data["matches"], key=lambda item: item["kickoff_at"])]


@router.get("/matches/{match_id}")
def match(match_id: int) -> dict:
    data = seed()
    item = find_one("matches", match_id)
    if not item:
        raise HTTPException(404, "Match not found")
    broadcasts = [
        broadcast
        for broadcast in data["broadcasts"]
        if broadcast["match_id"] == match_id
        and is_official_broadcast_link(broadcast["stream_url"], settings.broadcaster_hosts)
        and is_official_broadcast_link(broadcast["replay_url"], settings.broadcaster_hosts)
    ]
    return enrich_match(item, data) | {"broadcasts": broadcasts}


@router.get("/matches/{match_id}/events")
def match_events(match_id: int) -> list[dict]:
    data = seed()
    if not any(match["id"] == match_id for match in data["matches"]):
        raise HTTPException(404, "Match not found")

    players_by_id = {player["id"]: player for player in data["players"]}
    teams_by_id = {team["id"]: team for team in data["teams"]}
    events = [event for event in data["events"] if event["match_id"] == match_id]
    return [
        event
        | {
            "player": players_by_id.get(event.get("player_id")),
            "assist_player": players_by_id.get(event.get("assist_player_id")),
            "team": teams_by_id.get(event.get("team_id")),
        }
        for event in sorted(
            events,
            key=lambda item: (item["minute"], item.get("extra_minute") or 0, item["id"]),
        )
    ]


@router.get("/matches/{match_id}/lineups")
def match_lineups(match_id: int) -> list[dict]:
    data = seed()
    lineups = [lineup for lineup in data["lineups"] if lineup["match_id"] == match_id]
    players_by_id = {player["id"]: player for player in data["players"]}
    output = []
    for lineup in lineups:
        lineup_players = [
            item | {"player": players_by_id[item["player_id"]]}
            for item in data["lineup_players"]
            if item["lineup_id"] == lineup["id"]
        ]
        output.append(lineup | {"players": lineup_players})
    return output


@router.get("/matches/{match_id}/prediction")
def model_prediction(match_id: int, model_id: str = "country") -> dict:
    data = seed()
    match_item = find_one("matches", match_id)
    if not match_item:
        raise HTTPException(404, "Match not found")
    home = next(team for team in data["teams"] if team["id"] == match_item["home_team_id"])
    away = next(team for team in data["teams"] if team["id"] == match_item["away_team_id"])
    try:
        return predict_match(
            home,
            away,
            data["teams"],
            match_id,
            model_id=model_id,
            players=data["players"],
            matches=data["matches"],
        )
    except ValueError as exc:
        raise HTTPException(404, "Model not found") from exc


@router.get("/matches/{match_id}/live-probability")
def live_probability(match_id: int) -> dict:
    data = seed()
    snapshots = [snapshot for snapshot in data["live_snapshots"] if snapshot["match_id"] == match_id]
    if not snapshots:
        prediction = model_prediction(match_id)
        current = {
            "id": 0,
            "match_id": match_id,
            "minute": 0,
            "home_score": 0,
            "away_score": 0,
            "home_xg": 0.0,
            "away_xg": 0.0,
            "home_shots_on_target": 0,
            "away_shots_on_target": 0,
            "home_possession": None,
            "away_possession": None,
            "home_dangerous_attacks": 0,
            "away_dangerous_attacks": 0,
            "home_win_probability": prediction["home_win_probability"],
            "draw_probability": prediction["draw_probability"],
            "away_win_probability": prediction["away_win_probability"],
        }
        return {"current": current, "timeline": [], "what_changed": []}
    prematch = model_prediction(match_id)
    current = update_live_probability(prematch, snapshots[-1])
    return {
        "current": snapshots[-1] | current,
        "timeline": snapshots,
        "what_changed": probability_events(match_id, snapshots),
    }


@router.get("/live/matches/{match_id}/stream")
async def live_probability_stream(match_id: int):
    async def event_stream():
        payload = live_probability(match_id)
        yield f"event: snapshot\ndata: {json.dumps(payload, default=str)}\n\n"
        await asyncio.sleep(settings.live_poll_interval_seconds)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/predictions", dependencies=[Depends(prediction_write_rate_limit)])
def create_prediction(prediction: PredictionIn, db: Session | None = Depends(get_db)) -> dict:
    data = seed()
    validate_prediction_submission(prediction, data)
    prediction_dict = prediction.model_dump()
    prediction_dict["created_at"] = datetime.now(timezone.utc)
    prediction_dict["points"] = 0
    prediction_dict["scoring"] = None

    db_session = usable_db(db)
    if db_session:
        try:
            row = UserPredictionModel(
                **{key: value for key, value in prediction_dict.items() if key != "scoring"},
                scoring_json=None,
            )
            db_session.add(row)
            db_session.commit()
            db_session.refresh(row)
            return serialize_prediction(row) | {"teams_available": len(data["teams"])}
        except SQLAlchemyError:
            db_session.rollback()

    append_memory_prediction(prediction_dict)
    return prediction_dict | {"teams_available": len(data["teams"])}


@router.get("/predictions")
def list_predictions(
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_PUBLIC_PREDICTION_LIMIT,
            description="Return only the latest public predictions.",
        ),
    ] = DEFAULT_PUBLIC_PREDICTION_LIMIT,
    db: Session | None = Depends(get_db),
) -> list[dict]:
    db_session = usable_db(db)
    if db_session:
        try:
            rows = (
                db_session.query(UserPredictionModel)
                .order_by(desc(UserPredictionModel.created_at), desc(UserPredictionModel.id))
                .limit(limit)
                .all()
            )
            return [serialize_prediction(row) for row in reversed(rows)]
        except SQLAlchemyError:
            db_session.rollback()
    return USER_PREDICTIONS[-limit:]


@router.get("/leaderboards/top-scorers")
def top_scorers() -> list[dict]:
    data = seed()
    players_by_id = {player["id"]: player for player in data["players"]}
    teams_by_id = {team["id"]: team for team in data["teams"]}
    standings: dict[int, dict] = {
        player["id"]: {
            "player_id": player["id"],
            "player": player,
            "team": teams_by_id.get(player["team_id"]),
            "goals": player.get("tournament_goals", 0),
            "last_goal_minute": None,
        }
        for player in data["players"]
        if player.get("tournament_goals", 0) > 0
    }

    for event in data["events"]:
        if event.get("event_type") != "goal" or not event.get("player_id"):
            continue
        player = players_by_id.get(event["player_id"])
        if not player:
            continue
        team = teams_by_id.get(event.get("team_id") or player["team_id"])
        standing = standings.get(player["id"])
        if standing is None:
            continue
        standing["team"] = team
        standing["last_goal_minute"] = max(
            standing["last_goal_minute"] or 0, event.get("minute") or 0
        )

    provider_stats, _ = load_processed_player_stats()
    for stats in provider_stats:
        if stats.get("player_id") in standings or not stats.get("tournament_goals"):
            continue
        provider_id = int(stats.get("provider_player_id") or 0)
        synthetic_id = 1_000_000 + provider_id
        team = teams_by_id.get(stats.get("team_id"))
        provider_player = {
            "id": synthetic_id,
            "team_id": stats.get("team_id") or 0,
            "name": stats.get("name") or "Ukjent spiller",
            "position": stats.get("position") or "Ukjent",
            "shirt_number": 0,
            "age": 0,
            "club": team["name"] if team else "Ukjent",
            "caps": 0,
            "goals": 0,
            "tournament_goals": stats["tournament_goals"],
            "rating": 0,
        }
        standings[synthetic_id] = {
            "player_id": synthetic_id,
            "player": provider_player,
            "team": team,
            "goals": stats["tournament_goals"],
            "last_goal_minute": None,
        }

    return sorted(
        standings.values(),
        key=lambda item: (-item["goals"], item["last_goal_minute"] or 999, item["player"]["name"]),
    )[:20]


@router.get("/model/top-scorer-prediction")
def top_scorer_prediction() -> list[dict]:
    data = seed()
    model = get_model_config("country")
    teams_by_id = {team["id"]: team for team in data["teams"]}
    raw_scores = []

    for player in data["players"]:
        team = teams_by_id[player["team_id"]]
        goals_per_cap = (player.get("goals") or 0) / max(player.get("caps") or 1, 1)
        team_attack_proxy = ((team.get("elo_rating") or 1500) - 1400) / 800
        player_rating = (player.get("rating") or 70) / 100
        score = max(0.01, 0.45 * player_rating + 0.35 * goals_per_cap + 0.20 * team_attack_proxy)
        raw_scores.append((player, team, score))

    total = sum(score for _, _, score in raw_scores) or 1
    predictions = [
        {
            "player_id": player["id"],
            "player": player,
            "team": team,
            "probability": round(score / total, 4),
            "expected_goals": round(1.2 + score * 5, 2),
            "model_version": model.version,
            "signals": ["spiller-rating", "landslagsmål per kamp", "lagets Elo-proxy"],
        }
        for player, team, score in raw_scores
    ]
    return sorted(predictions, key=lambda item: item["probability"], reverse=True)[:20]


@router.get("/leaderboards/teams")
def team_leaderboard() -> list[dict]:
    return sorted(seed()["teams"], key=lambda team: (team["fifa_ranking"], -team["elo_rating"]))


@router.get("/leaderboards/groups")
def group_standings() -> list[dict]:
    data = seed()
    return calculate_group_standings(data["teams"], data["matches"])


@router.get("/model/features")
def model_features() -> dict:
    return {
        "features": FEATURES,
        "normalization": "Min-max-normalisering innen aktivt turneringsfelt. FIFA-rangering og mål imot per kamp inverteres.",
        "limitations": [
            "Økonomi og befolkning er proxyer, ikke direkte årsaksvariabler.",
            "Seedet fotballpopularitet må erstattes med dokumentert deltakelses- eller surveydata.",
            "Rå sannsynligheter er deterministiske; Monte Carlo er eneste stokastiske lag.",
        ],
    }


@router.get("/model/versions")
def model_versions() -> list[dict]:
    return seed()["model_versions"]


def latest_model_forecast(model_id: str, data: dict) -> dict:
    model = get_model_config(model_id)
    scheduled = sorted(
        [match for match in data["matches"] if match.get("status") == "scheduled"],
        key=lambda match: match["kickoff_at"],
    )
    match_item = scheduled[0] if scheduled else sorted(data["matches"], key=lambda match: match["kickoff_at"])[-1]
    home = next(team for team in data["teams"] if team["id"] == match_item["home_team_id"])
    away = next(team for team in data["teams"] if team["id"] == match_item["away_team_id"])
    prediction = predict_match(
        home,
        away,
        data["teams"],
        match_item["id"],
        model_id=model.id,
        players=data["players"],
        matches=data["matches"],
    )
    match_winner = home if prediction["home_win_probability"] >= prediction["away_win_probability"] else away
    match_confidence = max(prediction["home_win_probability"], prediction["away_win_probability"])
    cup_ranked = sorted(
        (
            {
                "team": team,
                "strength": team_strength(team, data["teams"], model, data["players"], data["matches"])[0],
            }
            for team in data["teams"]
        ),
        key=lambda item: item["strength"],
        reverse=True,
    )
    cup_winner = cup_ranked[0]["team"]
    cup_confidence = cup_ranked[0]["strength"] / sum(item["strength"] for item in cup_ranked[:8])

    return {
        "model_id": model.id,
        "model_name": model.name,
        "model_version": model.version,
        "match": enrich_match(match_item, data),
        "match_prediction": prediction,
        "match_winner_team": match_winner,
        "match_winner_probability": round(match_confidence, 4),
        "cup_winner_team": cup_winner,
        "cup_winner_probability": round(cup_confidence, 4),
        "cup_top_five": [
            {
                "team": item["team"],
                "score": round(item["strength"], 4),
            }
            for item in cup_ranked[:5]
        ],
    }


@router.get("/model/lab")
def model_lab() -> dict:
    active_model = get_model_config("country")
    data = seed()
    return {
        "active_model_id": active_model.id,
        "models": available_models(),
        "model_forecasts": [
            latest_model_forecast(model["id"], data)
            for model in available_models()
        ],
        "version_history": data["model_versions"],
        "feature_importance": model_feature_importance(active_model.id),
        "backtesting": {
            "dataset": active_model.training_data,
            "accuracy": active_model.accuracy,
            "log_loss": active_model.log_loss,
            "brier_score": active_model.brier_score,
            "training_status": active_model.training_status,
        },
        "training_plan": [
            "Importer historiske VM-kamper fra Fjelstul/FIFA.",
            "Lås feature-generering per kampdato for å unngå datalekkasje.",
            "Tren enkel, land, avansert og ekspertmodell på samme split.",
            "Evaluer accuracy, log loss, Brier-score og kalibrering.",
            "Publiser bare modeller som har dokumentert datagrunnlag.",
        ],
        "chart_slots": {
            "calibration_chart": "Klar for ekte kalibreringsgraf når historisk backtest er koblet på.",
            "confusion_matrix": "Klar for forvekslingsmatrise per valgt modell.",
            "shap_explanation": "Klar for SHAP-lignende forklaring per prediksjon.",
        },
    }


@router.get("/historical-insights")
def historical_insights() -> dict:
    return HISTORICAL_INSIGHTS


@router.get("/tournament/simulation", dependencies=[Depends(simulation_rate_limit)])
def tournament_simulation(
    iterations: Annotated[
        int,
        Query(ge=1, le=10_000, description="Monte Carlo iterations, capped for public safety."),
    ] = 2_000,
) -> dict:
    return simulate_tournament(seed()["teams"], iterations=iterations)


@router.get("/matches/{match_id}/simulation", dependencies=[Depends(simulation_rate_limit)])
def match_simulation(
    match_id: int,
    iterations: Annotated[
        int,
        Query(ge=1, le=50_000, description="Monte Carlo iterations, capped for public safety."),
    ] = 10_000,
) -> dict:
    prediction = model_prediction(match_id)
    return simulate_match(
        prediction["expected_home_goals"],
        prediction["expected_away_goals"],
        iterations=iterations,
    )
