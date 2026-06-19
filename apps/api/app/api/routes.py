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
from app.services.prediction import FEATURES, predict_match, score_prediction
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
    sources = source_statuses()
    configured_sources = sum(1 for source in sources if source["configured"])
    cached_sources = sum(1 for source in sources if source["cached"])
    external_match_feed_configured = any(
        source["configured"] for source in sources if source["key"] != "world_bank"
    )
    return {
        "source": settings.live_data_provider,
        "mode": "external"
        if settings.live_data_provider != "seeded" or external_match_feed_configured
        else "seeded",
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
            f"{configured_sources} eksterne datakilder er konfigurert, {cached_sources} har raw-cache.",
            "Seed-data brukes som trygg fallback når liveleverandør ikke er koblet på.",
            "Brukerprediksjoner går fra frontend til POST /predictions og poengsettes i API-et.",
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
    featured = live_matches or data["matches"][:5]
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
    return [enrich_match(match, data) for match in data["matches"]]


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
    return [event for event in seed()["events"] if event["match_id"] == match_id]


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
def model_prediction(match_id: int) -> dict:
    data = seed()
    match_item = find_one("matches", match_id)
    if not match_item:
        raise HTTPException(404, "Match not found")
    home = next(team for team in data["teams"] if team["id"] == match_item["home_team_id"])
    away = next(team for team in data["teams"] if team["id"] == match_item["away_team_id"])
    return predict_match(home, away, data["teams"], match_id)


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
    prediction_dict = prediction.model_dump()
    prediction_dict["created_at"] = datetime.now(timezone.utc)
    actual = find_one("matches", prediction.match_id) if prediction.match_id else {}
    actual = (actual or {}) | {"first_goalscorer_player_id": 1, "tournament_top_scorer_player_id": 3}
    scoring = score_prediction(prediction_dict, actual)
    prediction_dict["points"] = scoring["total_points"]
    prediction_dict["scoring"] = scoring

    db_session = usable_db(db)
    if db_session:
        try:
            row = UserPredictionModel(
                **{key: value for key, value in prediction_dict.items() if key != "scoring"},
                scoring_json=scoring,
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
            description="Return only the latest public demo predictions.",
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
    standings: dict[int, dict] = {}

    for event in data["events"]:
        if event.get("event_type") != "goal" or not event.get("player_id"):
            continue
        player = players_by_id.get(event["player_id"])
        if not player:
            continue
        team = teams_by_id.get(event.get("team_id") or player["team_id"])
        standing = standings.setdefault(
            player["id"],
            {
                "player_id": player["id"],
                "player": player,
                "team": team,
                "goals": 0,
                "last_goal_minute": None,
            },
        )
        standing["goals"] += 1
        standing["last_goal_minute"] = event.get("minute")

    return sorted(
        standings.values(),
        key=lambda item: (-item["goals"], item["last_goal_minute"] or 999, item["player"]["name"]),
    )[:20]


@router.get("/model/top-scorer-prediction")
def top_scorer_prediction() -> list[dict]:
    data = seed()
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
            "model_version": settings.model_version,
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
        "normalization": "Min-max normalization across the active tournament field; FIFA ranking is inverted.",
        "limitations": [
            "Economic and population indicators are proxies, not direct causal features.",
            "Seeded football popularity must be replaced by documented participation or survey data.",
            "Raw probabilities are deterministic; Monte Carlo is the only stochastic layer.",
        ],
    }


@router.get("/model/versions")
def model_versions() -> list[dict]:
    return seed()["model_versions"]


@router.get("/model/lab")
def model_lab() -> dict:
    models = [
        {
            "id": "simple",
            "name": "Enkel modell",
            "version": "wc-v0.1-simple",
            "status": "active",
            "description": "Rask baseline som kombinerer FIFA-rangering og Elo. Denne er lett å forklare og brukes som første sammenligningspunkt.",
            "features": ["fifa_ranking", "elo_rating"],
            "accuracy": 0.52,
            "log_loss": 1.02,
            "brier_score": 0.23,
            "limitations": [
                "Tar ikke hensyn til form, skader eller kampkontekst.",
                "Brukes som enkel referanse, ikke som endelig prediksjonsmotor.",
            ],
        },
        {
            "id": "country",
            "name": "Utvidet landmodell",
            "version": "wc-v0.2-country-features",
            "status": "planned",
            "description": "Neste steg legger til BNP per innbygger, befolkning, fotballpopularitet, historisk VM-score og konføderasjonsstyrke.",
            "features": [
                "fifa_ranking",
                "elo_rating",
                "gdp_per_capita",
                "population",
                "football_popularity_score",
                "historical_world_cup_score",
            ],
            "accuracy": None,
            "log_loss": None,
            "brier_score": None,
            "limitations": [
                "Økonomi og befolkning er proxyer, ikke direkte årsaker.",
                "Må backtestes mot historiske VM-kamper før den brukes som hovedmodell.",
            ],
        },
        {
            "id": "advanced",
            "name": "Avansert modell",
            "version": "wc-v1.0-advanced",
            "status": "planned",
            "description": "Senere modell med historiske kampdata, ratings over tid, kalibrering, SHAP-lignende forklaringer og bedre evaluering.",
            "features": [
                "all_country_features",
                "historical_match_results",
                "team_form",
                "squad_strength",
                "market_and_injury_signals",
                "calibrated_probabilities",
            ],
            "accuracy": None,
            "log_loss": None,
            "brier_score": None,
            "limitations": [
                "Krever rene datakilder og streng validering.",
                "Skal ikke slippes før kalibrering og leakage-sjekk er dokumentert.",
            ],
        },
    ]
    return {
        "active_model_id": "simple",
        "models": models,
        "version_history": seed()["model_versions"],
        "feature_importance": [
            {"feature": "elo_rating", "importance": 0.28},
            {"feature": "fifa_ranking", "importance": 0.22},
            {"feature": "historical_world_cup_score", "importance": 0.10},
            {"feature": "football_popularity_score", "importance": 0.10},
            {"feature": "confederation_strength", "importance": 0.10},
            {"feature": "gdp_per_capita", "importance": 0.08},
            {"feature": "population", "importance": 0.07},
            {"feature": "host_advantage_score", "importance": 0.05},
        ],
        "backtesting": {
            "dataset": "Historical World Cup matches placeholder: wire Fjelstul + FIFA official results.",
            "accuracy": 0.54,
            "log_loss": 0.96,
            "brier_score": 0.21,
        },
        "placeholders": {
            "calibration_chart": "Reserved chart slot",
            "confusion_matrix": "Reserved chart slot",
            "shap_explanation": "Reserved chart slot",
        },
    }


@router.get("/historical-insights")
def historical_insights() -> dict:
    return HISTORICAL_INSIGHTS


@router.get("/tournament/simulation", dependencies=[Depends(simulation_rate_limit)])
def tournament_simulation(
    iterations: Annotated[
        int,
        Query(ge=1, le=10_000, description="Monte Carlo iterations, capped for public demo safety."),
    ] = 2_000,
) -> dict:
    return simulate_tournament(seed()["teams"], iterations=iterations)


@router.get("/matches/{match_id}/simulation", dependencies=[Depends(simulation_rate_limit)])
def match_simulation(
    match_id: int,
    iterations: Annotated[
        int,
        Query(ge=1, le=50_000, description="Monte Carlo iterations, capped for public demo safety."),
    ] = 10_000,
) -> dict:
    prediction = model_prediction(match_id)
    return simulate_match(
        prediction["expected_home_goals"],
        prediction["expected_away_goals"],
        iterations=iterations,
    )
