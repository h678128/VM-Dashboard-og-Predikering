import { matchStageLabel, teamName } from "./labels";
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
    if (!match.group_name || match.home_team_id == null || match.away_team_id == null) continue;
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
          match.home_team_id == null ||
          match.away_team_id == null ||
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

export type TeamTournamentStatus = {
  kind: "active" | "eliminated" | "champion" | "pending";
  title: string;
  detail: string;
  match?: Match;
  opponent?: Team;
};

const eliminationStageTitles: Record<string, string> = {
  "Round of 32": "Røk ut i 16-delsfinalen",
  "Round of 16": "Røk ut i åttedelsfinalen",
  Quarterfinal: "Røk ut i kvartfinalen",
  "Quarter-final": "Røk ut i kvartfinalen",
  Semifinal: "Røk ut i semifinalen",
  "Semi-final": "Røk ut i semifinalen",
  Final: "Røk ut i finalen"
};

function opponentFor(match: Match, teamId: number): Team | undefined {
  return (match.home_team_id === teamId ? match.away_team : match.home_team) ?? undefined;
}

function teamLost(match: Match, teamId: number): boolean {
  if (match.status !== "finished" || match.home_score == null || match.away_score == null) return false;
  const isHome = match.home_team_id === teamId;
  const teamScore = isHome ? match.home_score : match.away_score;
  const opponentScore = isHome ? match.away_score : match.home_score;
  if (teamScore !== opponentScore) return teamScore < opponentScore;
  const teamPenalties = isHome ? match.home_penalty_score : match.away_penalty_score;
  const opponentPenalties = isHome ? match.away_penalty_score : match.home_penalty_score;
  return teamPenalties != null && opponentPenalties != null && teamPenalties < opponentPenalties;
}

function resultLabel(match: Match, teamId: number): string {
  const isHome = match.home_team_id === teamId;
  const teamScore = isHome ? match.home_score : match.away_score;
  const opponentScore = isHome ? match.away_score : match.home_score;
  const teamPenalties = isHome ? match.home_penalty_score : match.away_penalty_score;
  const opponentPenalties = isHome ? match.away_penalty_score : match.home_penalty_score;
  const regularScore = `${teamScore ?? "-"}–${opponentScore ?? "-"}`;
  return teamPenalties != null && opponentPenalties != null
    ? `${regularScore} (${teamPenalties}–${opponentPenalties} på straffer)`
    : regularScore;
}

export function getTeamTournamentStatus(teamId: number, matches: Match[]): TeamTournamentStatus {
  const teamMatches = matches
    .filter((match) => match.home_team_id === teamId || match.away_team_id === teamId)
    .sort((first, second) => new Date(first.kickoff_at).getTime() - new Date(second.kickoff_at).getTime());
  const knockoutLoss = [...teamMatches]
    .reverse()
    .find((match) => !match.group_name && match.stage !== "Match for third place" && teamLost(match, teamId));

  if (knockoutLoss) {
    const opponent = opponentFor(knockoutLoss, teamId);
    return {
      kind: "eliminated",
      title: eliminationStageTitles[knockoutLoss.stage] ?? `Røk ut i ${matchStageLabel(knockoutLoss.stage).toLowerCase()}`,
      detail: `Tapte ${resultLabel(knockoutLoss, teamId)}${opponent ? ` mot ${teamName(opponent)}` : ""}.`,
      match: knockoutLoss,
      opponent
    };
  }

  const final = teamMatches.find((match) => match.stage === "Final" && match.status === "finished");
  if (final && !teamLost(final, teamId)) {
    return { kind: "champion", title: "Verdensmester", detail: "Vant VM-finalen.", match: final, opponent: opponentFor(final, teamId) };
  }

  const groupMatches = teamMatches.filter((match) => match.group_name);
  const groupIsComplete = groupMatches.length >= 3 && groupMatches.every((match) => match.status === "finished");
  const qualifiedForKnockout = teamMatches.some((match) => match.stage === "Round of 32");
  if (groupIsComplete && !qualifiedForKnockout) {
    const lastGroupMatch = groupMatches[groupMatches.length - 1];
    const opponent = opponentFor(lastGroupMatch, teamId);
    return {
      kind: "eliminated",
      title: "Røk ut i gruppespillet",
      detail: opponent ? `Siste gruppekamp var mot ${teamName(opponent)}.` : "Ble slått ut etter gruppespillet.",
      match: lastGroupMatch,
      opponent
    };
  }

  if (qualifiedForKnockout) {
    const nextMatch = teamMatches.find((match) => match.status !== "finished");
    const opponent = nextMatch ? opponentFor(nextMatch, teamId) : undefined;
    return {
      kind: "active",
      title: "Fortsatt med i turneringen",
      detail: nextMatch
        ? `Neste kamp${opponent ? ` er mot ${teamName(opponent)}` : ""}: ${matchStageLabel(nextMatch.stage)}.`
        : "Venter på at neste utslagskamp skal bli avgjort.",
      match: nextMatch,
      opponent
    };
  }

  return {
    kind: "pending",
    title: "Turneringsstatus ikke avgjort",
    detail: "Status oppdateres når kampresultatene er bekreftet."
  };
}
