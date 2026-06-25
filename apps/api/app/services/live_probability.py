from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SIGNIFICANT_DELTA = 0.05


def clamp_probability(value: float) -> float:
    return max(0.02, min(0.96, value))


def update_live_probability(prematch: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    home = prematch["home_win_probability"]
    away = prematch["away_win_probability"]
    draw = prematch["draw_probability"]
    minute = snapshot["minute"]
    score_delta = snapshot["home_score"] - snapshot["away_score"]
    xg_delta = snapshot["home_xg"] - snapshot["away_xg"]
    sot_delta = snapshot["home_shots_on_target"] - snapshot["away_shots_on_target"]
    attack_delta = snapshot["home_dangerous_attacks"] - snapshot["away_dangerous_attacks"]
    red_delta = snapshot["away_red_cards"] - snapshot["home_red_cards"]

    time_pressure = min(1.0, minute / 90)
    score_push = score_delta * (0.10 + 0.22 * time_pressure)
    stat_push = xg_delta * 0.05 + sot_delta * 0.018 + attack_delta * 0.002
    red_card_push = red_delta * 0.12
    yellow_risk_push = (snapshot["away_yellow_cards"] - snapshot["home_yellow_cards"]) * 0.01

    new_home = clamp_probability(home + score_push + stat_push + red_card_push + yellow_risk_push)
    new_away = clamp_probability(away - score_push - stat_push - red_card_push - yellow_risk_push)
    new_draw = clamp_probability(draw + (0.08 if score_delta == 0 and minute > 60 else -abs(score_delta) * 0.05))
    total = new_home + new_draw + new_away

    probabilities = {
        "home_win_probability": round(new_home / total, 4),
        "draw_probability": round(new_draw / total, 4),
        "away_win_probability": round(new_away / total, 4),
    }
    probabilities["explanation"] = explain_change(prematch, snapshot, probabilities)
    return probabilities


def explain_change(previous: dict[str, Any], snapshot: dict[str, Any], current: dict[str, float]) -> list[dict[str, Any]]:
    previous_home = previous["home_win_probability"]
    delta = current["home_win_probability"] - previous_home
    reasons: list[dict[str, Any]] = []
    score_state = f"{snapshot['home_score']}-{snapshot['away_score']}"

    if abs(delta) >= SIGNIFICANT_DELTA:
        if snapshot["home_score"] != snapshot.get("previous_home_score", 0) or snapshot["away_score"] != snapshot.get("previous_away_score", 0):
            event_type = "goal"
        elif snapshot["home_red_cards"] or snapshot["away_red_cards"]:
            event_type = "red_card"
        elif abs(snapshot["home_xg"] - snapshot["away_xg"]) >= 0.4:
            event_type = "xg_swing"
        elif abs(snapshot["home_shots_on_target"] - snapshot["away_shots_on_target"]) >= 2:
            event_type = "shot_momentum"
        elif snapshot["minute"] >= 60:
            event_type = "match_minute_and_score_state"
        else:
            event_type = "formation_change"

        reasons.append(
            {
                "event_type": event_type,
                "minute": snapshot["minute"],
                "score_state": score_state,
                "probability_delta": round(delta, 4),
                "explanation": (
                    f"Home win probability moved {delta:+.1%} at {snapshot['minute']}' "
                    f"with score {score_state}. Main signal: {event_type.replace('_', ' ')}."
                ),
                "factors": {
                    "goal": score_state,
                    "red_card": {"home": snapshot["home_red_cards"], "away": snapshot["away_red_cards"]},
                    "xg_swing": round(snapshot["home_xg"] - snapshot["away_xg"], 2),
                    "shot_momentum": snapshot["home_shots_on_target"] - snapshot["away_shots_on_target"],
                    "substitution": "Krever livehendelser fra provider-feed.",
                    "formation_change": "Krever lineup- og formasjonsdata fra provider-feed.",
                    "yellow_card_risk": snapshot["away_yellow_cards"] - snapshot["home_yellow_cards"],
                    "match_minute_and_score_state": {"minute": snapshot["minute"], "score": score_state},
                },
            }
        )
    return reasons


def probability_events(match_id: int, snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events = []
    for index in range(1, len(snapshots)):
        previous = snapshots[index - 1]
        current = snapshots[index]
        delta = current["home_win_probability"] - previous["home_win_probability"]
        if abs(delta) < SIGNIFICANT_DELTA:
            continue
        explanation = explain_change(previous, current | {"previous_home_score": previous["home_score"], "previous_away_score": previous["away_score"]}, current)
        if not explanation:
            continue
        item = explanation[0]
        events.append(
            {
                "id": len(events) + 1,
                "match_id": match_id,
                "snapshot_id": current["id"],
                "minute": current["minute"],
                "score_state": item["score_state"],
                "event_type": item["event_type"],
                "previous_home_win_probability": previous["home_win_probability"],
                "current_home_win_probability": current["home_win_probability"],
                "probability_delta": round(delta, 4),
                "explanation": item["explanation"],
                "factors_json": item["factors"],
                "created_at": datetime.now(timezone.utc),
            }
        )
    return events

