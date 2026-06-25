import type { GroupStandings, Match, Team } from "./types";

export function calculateGroupStandings(teams: Team[], matches: Match[]): GroupStandings[] {
  const teamsById = new Map(teams.map((team) => [team.id, team]));
  const groupTeams = new Map<string, Set<number>>();

  for (const team of teams) {
    if (!team.group_name) continue;
    const ids = groupTeams.get(team.group_name) ?? new Set<number>();
    ids.add(team.id);
    groupTeams.set(team.group_name, ids);
  }

  for (const match of matches) {
    if (!match.group_name) continue;
    const ids = groupTeams.get(match.group_name) ?? new Set<number>();
    ids.add(match.home_team_id);
    ids.add(match.away_team_id);
    groupTeams.set(match.group_name, ids);
  }

  return [...groupTeams.entries()]
    .sort(([first], [second]) => first.localeCompare(second))
    .map(([group_name, teamIds]) => {
      const rows = new Map(
        [...teamIds].map((team_id) => [
          team_id,
          {
            position: 0,
            team_id,
            team: teamsById.get(team_id)!,
            played: 0,
            won: 0,
            drawn: 0,
            lost: 0,
            goals_for: 0,
            goals_against: 0,
            goal_difference: 0,
            points: 0
          }
        ])
      );

      for (const match of matches) {
        if (
          match.group_name !== group_name ||
          match.status !== "finished" ||
          match.home_score == null ||
          match.away_score == null
        ) {
          continue;
        }

        const home = rows.get(match.home_team_id)!;
        const away = rows.get(match.away_team_id)!;
        home.played += 1;
        away.played += 1;
        home.goals_for += match.home_score;
        home.goals_against += match.away_score;
        away.goals_for += match.away_score;
        away.goals_against += match.home_score;

        if (match.home_score > match.away_score) {
          home.won += 1;
          home.points += 3;
          away.lost += 1;
        } else if (match.away_score > match.home_score) {
          away.won += 1;
          away.points += 3;
          home.lost += 1;
        } else {
          home.drawn += 1;
          away.drawn += 1;
          home.points += 1;
          away.points += 1;
        }
      }

      const standings = [...rows.values()]
        .map((row) => ({
          ...row,
          goal_difference: row.goals_for - row.goals_against
        }))
        .sort(
          (first, second) =>
            second.points - first.points ||
            second.goal_difference - first.goal_difference ||
            second.goals_for - first.goals_for ||
            first.team.fifa_ranking - second.team.fifa_ranking ||
            first.team.name.localeCompare(second.team.name)
        )
        .map((row, index) => ({ ...row, position: index + 1 }));

      return { group_name, standings };
    });
}
