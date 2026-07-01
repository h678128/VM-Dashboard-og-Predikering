import type { Match, Team } from "./types";

export const APP_NAME = "VM Dashboard og Predikering";

const teamNames: Record<string, string> = {
  Norway: "Norge",
  France: "Frankrike",
  Senegal: "Senegal",
  Iraq: "Irak",
  Argentina: "Argentina",
  Algeria: "Algerie",
  Austria: "Østerrike",
  Jordan: "Jordan",
  Portugal: "Portugal",
  "DR Congo": "DR Kongo",
  Uzbekistan: "Usbekistan",
  Colombia: "Colombia",
  England: "England",
  Croatia: "Kroatia",
  Ghana: "Ghana",
  Panama: "Panama",
  Mexico: "Mexico",
  "South Africa": "Sør-Afrika",
  "South Korea": "Sør-Korea",
  "Czech Republic": "Tsjekkia",
  Canada: "Canada",
  "Bosnia and Herzegovina": "Bosnia-Hercegovina",
  Qatar: "Qatar",
  Switzerland: "Sveits",
  Brazil: "Brasil",
  Morocco: "Marokko",
  Haiti: "Haiti",
  Scotland: "Skottland",
  "United States": "USA",
  Paraguay: "Paraguay",
  Australia: "Australia",
  Turkey: "Tyrkia",
  Germany: "Tyskland",
  Curacao: "Curaçao",
  "Ivory Coast": "Elfenbenskysten",
  Ecuador: "Ecuador",
  Netherlands: "Nederland",
  Japan: "Japan",
  Sweden: "Sverige",
  Tunisia: "Tunisia",
  Belgium: "Belgia",
  Egypt: "Egypt",
  Iran: "Iran",
  "New Zealand": "New Zealand",
  Spain: "Spania",
  "Cape Verde": "Kapp Verde",
  "Saudi Arabia": "Saudi-Arabia",
  Uruguay: "Uruguay"
};

const stageLabels: Record<string, string> = {
  "Group stage": "Gruppespill",
  "Round of 32": "16-delsfinale",
  "Round of 16": "Åttedelsfinale",
  Quarterfinal: "Kvartfinale",
  "Quarter-final": "Kvartfinale",
  Semifinal: "Semifinale",
  "Semi-final": "Semifinale",
  "Match for third place": "Bronsefinale",
  Final: "Finale"
};

const statusLabels: Record<Match["status"], string> = {
  scheduled: "Ikke startet",
  live: "Direkte",
  finished: "Ferdig"
};

const eventLabels: Record<string, string> = {
  goal: "Mål",
  own_goal: "Selvmål",
  yellow_card: "Gult kort",
  red_card: "Rødt kort",
  penalty_missed: "Straffebom",
  var: "VAR",
  xg_swing: "xG-sving",
  shot_momentum: "Skuddtrykk",
  substitution: "Bytte",
  formation_change: "Formasjonsendring",
  yellow_card_risk: "Gulkort-risiko",
  match_minute_and_score_state: "Minutt og kampbilde"
};

const featureLabels: Record<string, string> = {
  elo_rating: "Elo-rating",
  fifa_ranking: "FIFA-rangering",
  fifa_ranking_points: "FIFA-poeng",
  historical_world_cup_score: "Historisk VM-score",
  football_popularity_score: "Fotballpopularitet",
  confederation_strength: "Konføderasjonsstyrke",
  gdp_per_capita: "BNP per innbygger",
  population: "Befolkning",
  host_advantage_score: "Vertsnasjonsfordel",
  average_player_rating: "Snitt-rating i tropp",
  top_player_rating: "Beste spiller-rating",
  striker_rating: "Angrepsrating",
  squad_caps: "Landskamperfaring",
  player_goal_rate: "Målsnitt i tropp",
  attacking_depth: "Angrepsdybde",
  current_group_points: "Nåværende gruppepoeng",
  recent_goal_difference: "Nylig målforskjell",
  goals_for_per_match: "Mål for per kamp",
  goals_against_per_match: "Mål imot per kamp",
  upset_resilience_proxy: "Underdog-robusthet",
  tournament_experience_proxy: "Turneringserfaring"
};

const metricLabels: Record<string, string> = {
  accuracy: "Treffsikkerhet",
  log_loss: "Log loss",
  brier_score: "Brier-score"
};

export function teamName(team: Team | string | null | undefined): string {
  if (!team) return "Ikke avgjort";
  const name = typeof team === "string" ? team : team.name;
  return teamNames[name] ?? name;
}

export function matchParticipantName(match: Match, side: "home" | "away"): string {
  const team = side === "home" ? match.home_team : match.away_team;
  const label = side === "home" ? match.home_team_label : match.away_team_label;
  return team ? teamName(team) : label ?? "Ikke avgjort";
}

export function matchStageLabel(stage: string): string {
  return stageLabels[stage] ?? stage;
}

export function matchStatusLabel(status: Match["status"]): string {
  return statusLabels[status] ?? status;
}

export function probabilityEventLabel(eventType: string): string {
  return eventLabels[eventType] ?? eventType.replaceAll("_", " ");
}

export function featureLabel(feature: string): string {
  return featureLabels[feature] ?? feature.replaceAll("_", " ");
}

export function metricLabel(metric: string): string {
  return metricLabels[metric] ?? metric.replaceAll("_", " ");
}
