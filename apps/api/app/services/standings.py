from __future__ import annotations

from typing import Any


def calculate_group_standings(teams: list[dict], matches: list[dict]) -> list[dict[str, Any]]:
    teams_by_id = {team["id"]: team for team in teams}
    groups: dict[str, set[int]] = {}

    for team in teams:
        group_name = team.get("group_name")
        if group_name:
            groups.setdefault(group_name, set()).add(team["id"])

    for match in matches:
        group_name = match.get("group_name")
        if not group_name:
            continue
        groups.setdefault(group_name, set()).update(
            [match["home_team_id"], match["away_team_id"]]
        )

    result = []
    for group_name in sorted(groups):
        rows = {
            team_id: {
                "team_id": team_id,
                "team": teams_by_id[team_id],
                "played": 0,
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
                "points": 0,
            }
            for team_id in groups[group_name]
        }

        for match in matches:
            if match.get("group_name") != group_name or match.get("status") != "finished":
                continue
            if match.get("home_score") is None or match.get("away_score") is None:
                continue

            home = rows[match["home_team_id"]]
            away = rows[match["away_team_id"]]
            home_score = match["home_score"]
            away_score = match["away_score"]

            home["played"] += 1
            away["played"] += 1
            home["goals_for"] += home_score
            home["goals_against"] += away_score
            away["goals_for"] += away_score
            away["goals_against"] += home_score

            if home_score > away_score:
                home["won"] += 1
                home["points"] += 3
                away["lost"] += 1
            elif away_score > home_score:
                away["won"] += 1
                away["points"] += 3
                home["lost"] += 1
            else:
                home["drawn"] += 1
                away["drawn"] += 1
                home["points"] += 1
                away["points"] += 1

        for row in rows.values():
            row["goal_difference"] = row["goals_for"] - row["goals_against"]

        ordered = sorted(
            rows.values(),
            key=lambda row: (
                -row["points"],
                -row["goal_difference"],
                -row["goals_for"],
                row["team"]["fifa_ranking"],
                row["team"]["name"],
            ),
        )
        for position, row in enumerate(ordered, start=1):
            row["position"] = position

        result.append({"group_name": group_name, "standings": ordered})

    return result
