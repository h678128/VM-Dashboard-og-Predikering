from __future__ import annotations

import random
from collections import Counter, defaultdict
from itertools import combinations
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

CONFEDERATION_STRENGTH = {
    "UEFA": 1.0,
    "CONMEBOL": 0.98,
    "CONCACAF": 0.72,
    "CAF": 0.70,
    "AFC": 0.64,
    "OFC": 0.45,
}

# Official FIFA match slots. Third-placed teams are assigned only to a slot
# whose published placeholder includes their group.
ROUND_OF_32_SLOTS: list[tuple[int, tuple[str, str], tuple[str, str | frozenset[str]]]] = [
    (73, ("runner_up", "A"), ("runner_up", "B")),
    (74, ("winner", "E"), ("third", frozenset("ABCDF"))),
    (75, ("winner", "F"), ("runner_up", "C")),
    (76, ("winner", "C"), ("runner_up", "F")),
    (77, ("winner", "I"), ("third", frozenset("CDFGH"))),
    (78, ("runner_up", "E"), ("runner_up", "I")),
    (79, ("winner", "A"), ("third", frozenset("CEFHI"))),
    (80, ("winner", "L"), ("third", frozenset("EHIJK"))),
    (81, ("winner", "D"), ("third", frozenset("BEFIJ"))),
    (82, ("winner", "G"), ("third", frozenset("AEHIJ"))),
    (83, ("runner_up", "K"), ("runner_up", "L")),
    (84, ("winner", "H"), ("runner_up", "J")),
    (85, ("winner", "B"), ("third", frozenset("EFGIJ"))),
    (86, ("winner", "J"), ("runner_up", "H")),
    (87, ("winner", "K"), ("third", frozenset("DEIJL"))),
    (88, ("runner_up", "D"), ("runner_up", "G")),
]

ROUND_OF_16_SLOTS = [
    (89, 74, 77),
    (90, 73, 75),
    (91, 76, 78),
    (92, 79, 80),
    (93, 83, 84),
    (94, 81, 82),
    (95, 86, 88),
    (96, 85, 87),
]
QUARTERFINAL_SLOTS = [(97, 89, 90), (98, 93, 94), (99, 91, 92), (100, 95, 96)]
SEMIFINAL_SLOTS = [(101, 97, 98), (102, 99, 100)]
FINAL_SLOTS = [(104, 101, 102)]


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


def simulate_match(
    home_xg: float,
    away_xg: float,
    iterations: int = 10_000,
    seed: int = 2026,
) -> dict[str, Any]:
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


def team_power(team: dict[str, Any]) -> float:
    ranking = max(1, int(team.get("fifa_ranking") or 100))
    ranking_score = 1 - min(ranking - 1, 209) / 209
    elo_score = min(1.2, max(0.0, (float(team.get("elo_rating") or 1500) - 1300) / 800))
    popularity = float(team.get("football_popularity_score") or 0.5)
    history = float(team.get("historical_world_cup_score") or 0.0)
    confederation = CONFEDERATION_STRENGTH.get(team.get("confederation"), 0.6)
    host = float(team.get("host_advantage_score") or 0.0)
    return (
        0.50 * elo_score
        + 0.20 * ranking_score
        + 0.12 * history
        + 0.08 * popularity
        + 0.06 * confederation
        + 0.04 * host
    )


def expected_goals(home_power: float, away_power: float) -> tuple[float, float]:
    difference = home_power - away_power
    return (
        min(3.6, max(0.25, 1.30 + difference * 1.35)),
        min(3.6, max(0.25, 1.30 - difference * 1.35)),
    )


def finished_group_results(matches: list[dict[str, Any]]) -> dict[tuple[int, int], tuple[int, int]]:
    results: dict[tuple[int, int], tuple[int, int]] = {}
    for match in matches:
        if (
            match.get("status") != "finished"
            or match.get("home_score") is None
            or match.get("away_score") is None
            or not match.get("group_name")
        ):
            continue
        home_id = int(match["home_team_id"])
        away_id = int(match["away_team_id"])
        home_score = int(match["home_score"])
        away_score = int(match["away_score"])
        results[(home_id, away_id)] = (home_score, away_score)
        results[(away_id, home_id)] = (away_score, home_score)
    return results


def empty_group_row(team: dict[str, Any]) -> dict[str, Any]:
    return {
        "team": team,
        "played": 0,
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_difference": 0,
        "points": 0,
    }


def apply_group_result(
    home: dict[str, Any],
    away: dict[str, Any],
    home_score: int,
    away_score: int,
) -> None:
    home["played"] += 1
    away["played"] += 1
    home["goals_for"] += home_score
    home["goals_against"] += away_score
    away["goals_for"] += away_score
    away["goals_against"] += home_score
    home["goal_difference"] = home["goals_for"] - home["goals_against"]
    away["goal_difference"] = away["goals_for"] - away["goals_against"]
    if home_score > away_score:
        home["won"] += 1
        away["lost"] += 1
        home["points"] += 3
    elif away_score > home_score:
        away["won"] += 1
        home["lost"] += 1
        away["points"] += 3
    else:
        home["drawn"] += 1
        away["drawn"] += 1
        home["points"] += 1
        away["points"] += 1


def standing_key(row: dict[str, Any], powers: dict[int, float]) -> tuple[float, ...]:
    team = row["team"]
    return (
        float(row["points"]),
        float(row["goal_difference"]),
        float(row["goals_for"]),
        -float(team.get("fifa_ranking") or 999),
        powers[team["id"]],
    )


def simulate_groups(
    groups: dict[str, list[dict[str, Any]]],
    powers: dict[int, float],
    known_results: dict[tuple[int, int], tuple[int, int]],
    rng: random.Random,
) -> dict[str, list[dict[str, Any]]]:
    standings: dict[str, list[dict[str, Any]]] = {}
    for group_name, group_teams in sorted(groups.items()):
        rows = {team["id"]: empty_group_row(team) for team in group_teams}
        for home, away in combinations(group_teams, 2):
            fixed_score = known_results.get((home["id"], away["id"]))
            if fixed_score:
                home_score, away_score = fixed_score
            else:
                home_xg, away_xg = expected_goals(powers[home["id"]], powers[away["id"]])
                home_score = poisson_sample(home_xg, rng)
                away_score = poisson_sample(away_xg, rng)
            apply_group_result(rows[home["id"]], rows[away["id"]], home_score, away_score)
        standings[group_name] = sorted(
            rows.values(),
            key=lambda row: standing_key(row, powers),
            reverse=True,
        )
    return standings


def rank_third_placed(
    group_standings: dict[str, list[dict[str, Any]]],
    powers: dict[int, float],
) -> list[dict[str, Any]]:
    third_placed = []
    for group_name, standings in group_standings.items():
        third_placed.append({**standings[2], "group_name": group_name})
    return sorted(third_placed, key=lambda row: standing_key(row, powers), reverse=True)


def assign_third_placed(third_placed: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    qualified_by_group = {row["group_name"]: row["team"] for row in third_placed[:8]}
    third_slots = [slot for slot in ROUND_OF_32_SLOTS if slot[2][0] == "third"]
    assignments: dict[int, dict[str, Any]] = {}

    ordered_slots = sorted(
        third_slots,
        key=lambda slot: len(set(slot[2][1]) & set(qualified_by_group)),
    )

    def search(index: int, unused_groups: set[str]) -> bool:
        if index == len(ordered_slots):
            return True
        match_number, _, opponent = ordered_slots[index]
        allowed_groups = set(opponent[1])
        for group_name in sorted(unused_groups & allowed_groups):
            assignments[match_number] = qualified_by_group[group_name]
            if search(index + 1, unused_groups - {group_name}):
                return True
            assignments.pop(match_number, None)
        return False

    if not search(0, set(qualified_by_group)):
        raise ValueError("Kunne ikke plassere de åtte beste treerne i FIFA-braketten.")
    return assignments


def resolve_group_slot(
    slot: tuple[str, str | frozenset[str]],
    group_standings: dict[str, list[dict[str, Any]]],
    third_assignments: dict[int, dict[str, Any]],
    match_number: int,
) -> dict[str, Any]:
    position, group = slot
    if position == "third":
        return third_assignments[match_number]
    index = 0 if position == "winner" else 1
    return group_standings[str(group)][index]["team"]


def knockout_match(
    match_number: int,
    stage: str,
    home: dict[str, Any],
    away: dict[str, Any],
    powers: dict[int, float],
    rng: random.Random,
) -> dict[str, Any]:
    home_xg, away_xg = expected_goals(powers[home["id"]], powers[away["id"]])
    home_score = poisson_sample(home_xg, rng)
    away_score = poisson_sample(away_xg, rng)
    decided_by = "regular_time"
    if home_score == away_score:
        decided_by = "penalties"
        home_probability = 1 / (1 + exp(-4 * (powers[home["id"]] - powers[away["id"]])))
        winner = home if rng.random() < home_probability else away
    else:
        winner = home if home_score > away_score else away
    return {
        "match_number": match_number,
        "stage": stage,
        "home_team": home,
        "away_team": away,
        "home_score": home_score,
        "away_score": away_score,
        "decided_by": decided_by,
        "winner_team": winner,
    }


def play_followup_round(
    slots: list[tuple[int, int, int]],
    previous_winners: dict[int, dict[str, Any]],
    stage: str,
    powers: dict[int, float],
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    matches = []
    winners = {}
    for match_number, home_source, away_source in slots:
        result = knockout_match(
            match_number,
            stage,
            previous_winners[home_source],
            previous_winners[away_source],
            powers,
            rng,
        )
        matches.append(result)
        winners[match_number] = result["winner_team"]
    return matches, winners


def simulate_knockout_bracket(
    group_standings: dict[str, list[dict[str, Any]]],
    third_placed: list[dict[str, Any]],
    powers: dict[int, float],
    rng: random.Random,
) -> dict[str, list[dict[str, Any]]]:
    third_assignments = assign_third_placed(third_placed)
    round_of_32 = []
    round_of_32_winners = {}
    for match_number, home_slot, away_slot in ROUND_OF_32_SLOTS:
        home = resolve_group_slot(home_slot, group_standings, third_assignments, match_number)
        away = resolve_group_slot(away_slot, group_standings, third_assignments, match_number)
        result = knockout_match(match_number, "round_of_32", home, away, powers, rng)
        round_of_32.append(result)
        round_of_32_winners[match_number] = result["winner_team"]

    round_of_16, round_of_16_winners = play_followup_round(
        ROUND_OF_16_SLOTS, round_of_32_winners, "round_of_16", powers, rng
    )
    quarterfinals, quarterfinal_winners = play_followup_round(
        QUARTERFINAL_SLOTS, round_of_16_winners, "quarterfinal", powers, rng
    )
    semifinals, semifinal_winners = play_followup_round(
        SEMIFINAL_SLOTS, quarterfinal_winners, "semifinal", powers, rng
    )
    final, _ = play_followup_round(FINAL_SLOTS, semifinal_winners, "final", powers, rng)
    return {
        "round_of_32": round_of_32,
        "round_of_16": round_of_16,
        "quarterfinal": quarterfinals,
        "semifinal": semifinals,
        "final": final,
    }


def stage_participants(bracket: dict[str, list[dict[str, Any]]], stage: str) -> list[int]:
    return [match["winner_team"]["id"] for match in bracket[stage]]


def validate_tournament_groups(groups: dict[str, list[dict[str, Any]]]) -> None:
    expected_groups = set("ABCDEFGHIJKL")
    if set(groups) != expected_groups or any(len(group) != 4 for group in groups.values()):
        raise ValueError("VM-simulatoren krever 12 grupper med fire lag i hver gruppe.")


def simulate_tournament(
    teams: list[dict[str, Any]],
    matches: list[dict[str, Any]] | None = None,
    iterations: int = 2_000,
    seed: int = 2026,
) -> dict[str, Any]:
    rng = random.Random(seed)
    counters: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for team in teams:
        groups[str(team.get("group_name") or "")].append(team)
    validate_tournament_groups(groups)

    powers = {team["id"]: team_power(team) for team in teams}
    known_results = finished_group_results(matches or [])
    example_groups: dict[str, list[dict[str, Any]]] = {}
    example_bracket: dict[str, list[dict[str, Any]]] = {}

    for iteration in range(iterations):
        group_standings = simulate_groups(groups, powers, known_results, rng)
        third_placed = rank_third_placed(group_standings, powers)
        qualified = [row["team"] for standings in group_standings.values() for row in standings[:2]]
        qualified.extend(row["team"] for row in third_placed[:8])
        for team in qualified:
            counters[team["id"]]["advance_group"] += 1
            counters[team["id"]]["round_of_32"] += 1

        bracket = simulate_knockout_bracket(group_standings, third_placed, powers, rng)
        for team_id in stage_participants(bracket, "round_of_32"):
            counters[team_id]["round_of_16"] += 1
        for team_id in stage_participants(bracket, "round_of_16"):
            counters[team_id]["quarterfinal"] += 1
        for team_id in stage_participants(bracket, "quarterfinal"):
            counters[team_id]["semifinal"] += 1
        for team_id in stage_participants(bracket, "semifinal"):
            counters[team_id]["final"] += 1
        champion_id = bracket["final"][0]["winner_team"]["id"]
        counters[champion_id]["winner"] += 1

        if iteration == 0:
            example_groups = group_standings
            example_bracket = bracket

    return {
        "iterations": iterations,
        "format": {
            "groups": 12,
            "teams_per_group": 4,
            "group_matches": 72,
            "automatic_qualifiers": 24,
            "best_third_placed_qualifiers": 8,
            "round_of_32_teams": 32,
        },
        "teams": [
            {
                "team_id": team["id"],
                "team": team,
                **{
                    stage: round(counters[team["id"]][stage] / iterations, 4)
                    for stage in STAGES
                },
            }
            for team in teams
        ],
        "example_groups": example_groups,
        "example_bracket": example_bracket,
        "model_notes": [
            "Ferdige gruppekamper beholdes som faste resultater; øvrige kamper simuleres.",
            "Gruppene rangeres på poeng, målforskjell, scorede mål og FIFA-ranking.",
            "Kortbasert fair-play og komplett innbyrdes tiebreak er ikke modellert ennå.",
            "Treerlag plasseres bare i kampplasser tillatt av FIFAs publiserte brakett.",
        ],
    }
