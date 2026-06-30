from __future__ import annotations

import random
from collections import Counter, defaultdict
from math import exp, factorial
from typing import Any


STAGES = [
    "advance_group",
    "round_of_32",
    "round_of_16",
    "quarterfinal",
    "semifinal",
    "final",
    "winner",
]


def poisson_sample(lam: float, rng: random.Random) -> int:
    threshold = exp(-lam)
    value = 1.0
    goals = 0
    while value > threshold:
        goals += 1
        value *= rng.random()
    return goals - 1


def likely_scores(home_xg: float, away_xg: float, max_goals: int = 5) -> list[dict[str, Any]]:
    outcomes = []
    for home in range(max_goals + 1):
        for away in range(max_goals + 1):
            hp = exp(-home_xg) * home_xg**home / factorial(home)
            ap = exp(-away_xg) * away_xg**away / factorial(away)
            outcomes.append({"score": f"{home}-{away}", "probability": round(hp * ap, 4)})
    return sorted(outcomes, key=lambda item: item["probability"], reverse=True)[:8]


def simulate_match(home_xg: float, away_xg: float, iterations: int = 10_000, seed: int = 2026) -> dict[str, Any]:
    rng = random.Random(seed)
    results: Counter[str] = Counter()
    scores: Counter[str] = Counter()
    for _ in range(iterations):
        home = poisson_sample(home_xg, rng)
        away = poisson_sample(away_xg, rng)
        scores[f"{home}-{away}"] += 1
        if home > away:
            results["home"] += 1
        elif away > home:
            results["away"] += 1
        else:
            results["draw"] += 1
    return {
        "iterations": iterations,
        "home_win_probability": round(results["home"] / iterations, 4),
        "draw_probability": round(results["draw"] / iterations, 4),
        "away_win_probability": round(results["away"] / iterations, 4),
        "most_likely_scores": [
            {"score": score, "probability": round(count / iterations, 4)}
            for score, count in scores.most_common(8)
        ],
    }


def simulate_tournament(teams: list[dict[str, Any]], iterations: int = 2_000, seed: int = 2026) -> dict[str, Any]:
    rng = random.Random(seed)
    counters: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    strength = {
        team["id"]: (
            (1 / max(team["fifa_ranking"], 1)) * 70
            + team["elo_rating"] / 2100
            + team["football_popularity_score"] * 0.2
            + team.get("historical_world_cup_score", 0) * 0.25
        )
        for team in teams
    }

    for _ in range(iterations):
        ordered = sorted(teams, key=lambda team: strength[team["id"]] + rng.random() * 0.18, reverse=True)
        for rank, team in enumerate(ordered):
            team_id = team["id"]
            if rank < 6:
                counters[team_id]["advance_group"] += 1
            if rank < 8:
                counters[team_id]["round_of_32"] += 1
            if rank < 6:
                counters[team_id]["round_of_16"] += 1
            if rank < 4:
                counters[team_id]["quarterfinal"] += 1
            if rank < 3:
                counters[team_id]["semifinal"] += 1
            if rank < 2:
                counters[team_id]["final"] += 1
            if rank == 0:
                counters[team_id]["winner"] += 1

    return {
        "iterations": iterations,
        "teams": [
            {
                "team_id": team["id"],
                "team": team,
                **{stage: round(counters[team["id"]][stage] / iterations, 4) for stage in STAGES},
            }
            for team in teams
        ],
    }

