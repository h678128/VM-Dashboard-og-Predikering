import { liveTimeline, matches, players, prediction, teams, whatChanged } from "./seed";
import { API_BASE_URL } from "./config";
import type {
  DataStatus,
  LiveSnapshot,
  Match,
  ModelPrediction,
  Player,
  ProbabilityEvent,
  Team,
  UserPrediction
} from "./types";

async function getJson<T>(path: string, fallback: T): Promise<T> {
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

export function formatOsloTime(value: string): string {
  return new Intl.DateTimeFormat("nb-NO", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Oslo"
  }).format(new Date(value));
}

export const api = {
  dataStatus: () => getJson<DataStatus>("/data/status", {
    source: "frontend-seed",
    mode: "seed-fallback",
    timezone: "Europe/Oslo",
    model_version: "wc-v0.2-norway",
    counts: {
      teams: teams.length,
      players: players.length,
      matches: matches.length,
      broadcasts: matches.reduce((count, match) => count + (match.broadcasts?.length ?? 0), 0),
      live_snapshots: liveTimeline.length,
      user_predictions: 0
    },
    data_flow: [
      "Frontend bruker seed fallback fordi API-et ikke svarte.",
      "Sett NEXT_PUBLIC_API_BASE_URL for å bruke deployet API.",
      "Når API-et svarer, går brukerprediksjoner til POST /predictions."
    ]
  }),
  matches: () => getJson<Match[]>("/matches", matches),
  match: (id: number) => getJson<Match>(`/matches/${validId(id) ? id : matches[0].id}`, matches.find((match) => match.id === id) ?? matches[0]),
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
  predictions: () => getJson<UserPrediction[]>("/predictions", []),
  prediction: (id: number) => getJson<ModelPrediction>(`/matches/${id}/prediction`, { ...prediction, match_id: id }),
  live: (id: number) => getJson<{ current: LiveSnapshot; timeline: LiveSnapshot[]; what_changed: ProbabilityEvent[] }>(`/matches/${id}/live-probability`, { current: liveTimeline[liveTimeline.length - 1], timeline: liveTimeline, what_changed: whatChanged }),
  historical: () => getJson<Record<string, unknown>>("/historical-insights", {}),
  modelLab: () => getJson<Record<string, unknown>>("/model/lab", {}),
  tournament: () => getJson<Record<string, unknown>>("/tournament/simulation", {})
};

