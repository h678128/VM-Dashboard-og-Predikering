import { API_BASE_URL, HAS_API_BASE_URL } from "./config";
import { matchStatusLabel, teamName } from "./labels";
import { events, lineups, liveTimeline, matches, modelLab, players, prediction, teams, topScorerPredictions, topScorers, whatChanged } from "./seed";
import { calculateGroupStandings } from "./standings";
import type {
  DataStatus,
  GroupStandings,
  LiveSnapshot,
  Lineup,
  LiveTickerPayload,
  Match,
  MatchEvent,
  ModelPrediction,
  Player,
  ProbabilityEvent,
  Team,
  TournamentSimulation,
  TopScorerPrediction,
  TopScorerStanding,
  UserPrediction
} from "./types";

async function getJson<T>(path: string, fallback: T): Promise<T> {
  if (!HAS_API_BASE_URL) return fallback;
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { next: { revalidate: 30 } });
    if (!response.ok) return fallback;
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

function validId(id: number): boolean {
  return Number.isInteger(id) && id > 0;
}

function liveFallback(matchId: number): { current: LiveSnapshot; timeline: LiveSnapshot[]; what_changed: ProbabilityEvent[] } {
  return {
    current: {
      id: 0,
      match_id: matchId,
      minute: 0,
      home_score: 0,
      away_score: 0,
      home_xg: 0,
      away_xg: 0,
      home_shots_on_target: 0,
      away_shots_on_target: 0,
      home_possession: null,
      away_possession: null,
      home_dangerous_attacks: 0,
      away_dangerous_attacks: 0,
      home_win_probability: prediction.home_win_probability,
      draw_probability: prediction.draw_probability,
      away_win_probability: prediction.away_win_probability
    },
    timeline: [],
    what_changed: []
  };
}

export function formatOsloTime(value: string): string {
  return new Intl.DateTimeFormat("nb-NO", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Oslo"
  }).format(new Date(value));
}

export const api = {
  dataStatus: () => getJson<DataStatus>("/data/status", {
    source: "FIFA World Cup 2026 fixtures and results",
    source_url: "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums",
    mode: "seed-fallback",
    is_live_data: false,
    last_updated: "2026-06-27T12:00:00+00:00",
    processed_at: "2026-06-28T10:00:00+00:00",
    timezone: "Europe/Oslo",
    model_version: "wc-v0.2-country-features",
    counts: {
      teams: teams.length,
      players: players.length,
      matches: matches.length,
      broadcasts: matches.reduce((count, match) => count + (match.broadcasts?.length ?? 0), 0),
      live_snapshots: liveTimeline.length,
      user_predictions: 0
    },
    data_flow: [
      "Frontend bruker et kilde-merket kamp-snapshot fordi NEXT_PUBLIC_API_BASE_URL ikke er satt.",
      "Når API-et er deployet, settes NEXT_PUBLIC_API_BASE_URL i Vercel.",
      "API-et eksponerer /data/sources for ekte datakilder og raw-cache status.",
      "Når API-et svarer, går brukerprediksjoner til POST /predictions."
    ]
  }),
  matches: () => getJson<Match[]>("/matches", matches),
  match: (id: number) => getJson<Match>(`/matches/${validId(id) ? id : matches[0].id}`, matches.find((match) => match.id === id) ?? matches[0]),
  matchEvents: (id: number) => getJson<MatchEvent[]>(`/matches/${validId(id) ? id : matches[0].id}/events`, events.filter((event) => event.match_id === id)),
  teams: () => getJson<Team[]>("/teams", teams),
  team: (id: number) => {
    const fallbackTeam = teams.find((team) => team.id === id) ?? teams[0];
    const safeId = validId(id) ? id : fallbackTeam.id;
    return getJson<Team & { players?: Player[] }>(`/teams/${safeId}`, {
      ...fallbackTeam,
      players: players.filter((player) => player.team_id === fallbackTeam.id)
    });
  },
  players: () => getJson<Player[]>("/players", players),
  player: (id: number) => getJson<Player>(`/players/${validId(id) ? id : players[0].id}`, players.find((player) => player.id === id) ?? players[0]),
  topScorers: () => getJson<TopScorerStanding[]>("/leaderboards/top-scorers", topScorers),
  groupStandings: () => getJson<GroupStandings[]>("/leaderboards/groups", calculateGroupStandings(teams, matches)),
  topScorerPredictions: () => getJson<TopScorerPrediction[]>("/model/top-scorer-prediction", topScorerPredictions),
  predictions: () => getJson<UserPrediction[]>("/predictions", []),
  lineups: (id: number) => getJson<Lineup[]>(`/matches/${id}/lineups`, lineups.filter((lineup) => lineup.match_id === id)),
  prediction: (id: number, modelId = "country") => getJson<ModelPrediction>(`/matches/${id}/prediction?model_id=${encodeURIComponent(modelId)}`, { ...prediction, match_id: id, model_id: modelId }),
  live: (id: number) => getJson<{ current: LiveSnapshot; timeline: LiveSnapshot[]; what_changed: ProbabilityEvent[] }>(
    `/matches/${id}/live-probability`,
    liveTimeline.length
      ? { current: liveTimeline[liveTimeline.length - 1], timeline: liveTimeline, what_changed: whatChanged }
      : liveFallback(id)
  ),
  historical: () => getJson<Record<string, unknown>>("/historical-insights", {}),
  modelLab: () => getJson<Record<string, unknown>>("/model/lab", modelLab),
  tournament: () => getJson<TournamentSimulation>("/tournament/simulation", {
    iterations: 0,
    format: {
      groups: 12,
      teams_per_group: 4,
      group_matches: 72,
      automatic_qualifiers: 24,
      best_third_placed_qualifiers: 8,
      round_of_32_teams: 32
    },
    teams: [],
    example_groups: {},
    example_bracket: {
      round_of_32: [],
      round_of_16: [],
      quarterfinal: [],
      semifinal: [],
      final: []
    },
    model_notes: []
  }),
  liveTicker: () => getJson<LiveTickerPayload>("/live/ticker", {
    mode: "scheduled",
    timezone: "Europe/Oslo",
    poll_interval_seconds: 30,
    items: [
      ...matches.slice(0, 5).map((match) => ({
        kind: "match" as const,
        label: `${teamName(match.home_team)} - ${teamName(match.away_team)} · ${match.status === "scheduled" ? "ikke startet" : `${match.home_score ?? 0}-${match.away_score ?? 0}`} · ${formatOsloTime(match.kickoff_at)} · ${matchStatusLabel(match.status)}`,
        match_id: match.id,
        status: match.status,
        kickoff_at: match.kickoff_at
      })),
      { kind: "meta" as const, label: "Alle tider vises i Europe/Oslo" },
      { kind: "meta" as const, label: "Kun offisielle norske TV-lenker: NRK, NRK TV, TV 2 og TV 2 Play" },
      { kind: "meta" as const, label: "Prediksjoner og modellforklaringer oppdateres når live-data er koblet på" }
    ]
  })
};
