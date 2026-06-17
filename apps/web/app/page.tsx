import { ArrowRight, CalendarDays, CircleDollarSign, Goal, Radio, ShieldCheck, Trophy, UsersRound, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { DataFlowStatus } from "@/components/DataFlowStatus";
import { LiveTopScorerTable, TeamLeaderboard, TopScorerPredictionTable } from "@/components/Leaderboards";
import { MatchCard } from "@/components/MatchCard";
import { TeamBadge } from "@/components/TeamBadge";
import { api, formatOsloTime } from "@/lib/api";
import { APP_NAME, matchStageLabel, matchStatusLabel, teamName } from "@/lib/labels";
import type { Team } from "@/lib/types";

type SimulationTeam = {
  team_id: number;
  team: Team;
  winner: number;
};

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function compactNumber(value: number): string {
  return new Intl.NumberFormat("nb-NO", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function StatCard({ label, value, helper, Icon }: { label: string; value: string | number; helper: string; Icon: LucideIcon }) {
  return (
    <div className="dashboard-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-white/60">{label}</p>
          <strong className="mt-5 block text-4xl font-black tracking-normal text-white">{value}</strong>
          <span className="mt-1 block text-sm text-white/60">{helper}</span>
        </div>
        <span className="grid size-10 place-items-center rounded-md bg-mint/10 text-mint">
          <Icon size={20} />
        </span>
      </div>
    </div>
  );
}

export default async function HomePage() {
  const [matches, teams, tournament, dataStatus, topScorers, topScorerPredictions] = await Promise.all([
    api.matches(),
    api.teams(),
    api.tournament(),
    api.dataStatus(),
    api.topScorers(),
    api.topScorerPredictions()
  ]);

  const liveMatch = matches.find((match) => match.status === "live") ?? null;
  const featuredMatch = liveMatch ?? matches[0];
  const upcomingMatches = matches.filter((match) => match.id !== featuredMatch.id).slice(0, 4);
  const officialBroadcasts = matches.reduce((count, match) => count + (match.broadcasts?.length ?? 0), 0);
  const goalsScored = matches.reduce((count, match) => count + (match.home_score ?? 0) + (match.away_score ?? 0), 0);
  const tournamentTeams = Array.isArray((tournament as { teams?: SimulationTeam[] }).teams)
    ? ((tournament as { teams: SimulationTeam[] }).teams ?? []).slice(0, 7)
    : teams
        .slice()
        .sort((first, second) => second.elo_rating - first.elo_rating)
        .slice(0, 7)
        .map((team, index) => ({ team_id: team.id, team, winner: Math.max(0.04, 0.18 - index * 0.018) }));
  const favorite = tournamentTeams[0];
  const confederations = teams.reduce<Record<string, number>>((acc, team) => {
    acc[team.confederation] = (acc[team.confederation] ?? 0) + 1;
    return acc;
  }, {});
  const confederationTotal = Object.values(confederations).reduce((sum, value) => sum + value, 0) || 1;
  const confederationSlices = Object.entries(confederations).map(([label, value]) => ({
    label,
    value,
    percent: value / confederationTotal
  }));
  const sliceOne = (confederationSlices[0]?.percent ?? 0) * 360;
  const sliceTwo = sliceOne + (confederationSlices[1]?.percent ?? 0) * 360;
  const sliceThree = sliceTwo + (confederationSlices[2]?.percent ?? 0) * 360;

  return (
    <div className="space-y-8">
      <section className="border-b border-white/10 pb-7">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div>
            <h1 className="text-4xl font-black uppercase tracking-[0.08em] text-white md:text-5xl">VM 2026</h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-white/60">
              {APP_NAME} samler kamper, norske sendelenker, spillerdata og modellstyrte prediksjoner i et deployklart analyse-dashboard.
            </p>
          </div>
          <span className="inline-flex items-center rounded-md bg-mint px-3 py-1 text-xs font-black uppercase tracking-[0.08em] text-night">
            USA · MEX · CAN
          </span>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard Icon={UsersRound} helper="i demo-datasettet" label="Lag" value={teams.length} />
        <StatCard Icon={CalendarDays} helper={`${matches.filter((match) => match.status === "scheduled").length} planlagt`} label="Kamper" value={matches.length} />
        <StatCard Icon={Goal} helper={goalsScored ? "registrert i kampdata" : "venter på ekte resultater"} label="Mål" value={goalsScored} />
        <StatCard Icon={Trophy} helper={favorite ? `${percent(favorite.winner)} vinnersjanse` : "modell ikke klar"} label="Favoritt" value={favorite ? favorite.team.fifa_code : "—"} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_465px]">
        <div className="dashboard-card">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="eyebrow">Tittelmodell</p>
              <h2 className="mt-1 text-xl font-black uppercase tracking-[0.05em]">Sannsynlighet for VM-gull</h2>
            </div>
            <Link className="secondary-action" href="/model">
              Modellverksted <ArrowRight size={16} />
            </Link>
          </div>

          <div className="flex h-[300px] items-end gap-3 border-b border-l border-white/10 px-3 pb-0 pt-6">
            {tournamentTeams.map((item) => {
              const value = Math.max(6, Math.round(item.winner * 100));
              return (
                <div key={item.team_id} className="flex h-full min-w-0 flex-1 flex-col justify-end gap-2">
                  <div className="w-full rounded-t-md bg-mint shadow-[0_0_28px_rgba(24,225,138,0.16)]" style={{ height: `${Math.min(92, value * 4.8)}%` }} />
                  <span className="text-center text-xs font-bold text-white/60">{item.team.fifa_code}</span>
                </div>
              );
            })}
          </div>

          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {tournamentTeams.slice(0, 4).map((item) => (
              <div key={item.team_id} className="soft-card flex items-center justify-between gap-3 p-3 text-sm">
                <TeamBadge compact inverted linked={false} team={item.team} />
                <strong className="text-mint">{percent(item.winner)}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="dashboard-card">
          <div className="mb-6 flex items-center justify-between gap-3">
            <div>
              <p className="eyebrow">Deltakelse</p>
              <h2 className="mt-1 text-xl font-black uppercase tracking-[0.05em]">Lag per konføderasjon</h2>
            </div>
            <ShieldCheck className="text-mint" size={24} />
          </div>

          <div className="grid place-items-center py-4">
            <div
              aria-label="Fordeling av lag per konføderasjon"
              className="size-48 rounded-full"
              style={{
                background: `conic-gradient(#18e18a 0deg ${sliceOne}deg, #ff6370 ${sliceOne}deg ${sliceTwo}deg, #f4c542 ${sliceTwo}deg ${sliceThree}deg, #7aa2ff ${sliceThree}deg 360deg)`
              }}
            >
              <div className="grid size-full place-items-center rounded-full p-10">
                <div className="grid size-28 place-items-center rounded-full bg-card text-center shadow-inner">
                  <span>
                    <strong className="block text-3xl">{teams.length}</strong>
                    <span className="text-xs text-white/50">lag</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-2">
            {confederationSlices.map((item, index) => (
              <div key={item.label} className="soft-card flex items-center justify-between p-3 text-sm">
                <span className="inline-flex items-center gap-2 font-semibold">
                  <span className={`size-2.5 rounded-full ${index === 0 ? "bg-mint" : index === 1 ? "bg-coral" : index === 2 ? "bg-gold" : "bg-fjord"}`} />
                  {item.label}
                </span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="dashboard-card">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="eyebrow">Kampflyt</p>
              <h2 className="mt-1 text-xl font-black uppercase tracking-[0.05em]">Neste kamper</h2>
            </div>
            <Link className="secondary-action" href="/matches">
              Alle kamper <ArrowRight size={16} />
            </Link>
          </div>
          <div className="grid gap-3 lg:grid-cols-2">
            {upcomingMatches.map((match) => <MatchCard key={match.id} match={match} />)}
          </div>
        </div>

        <div className="dashboard-card overflow-hidden p-0">
          <div className="border-b border-white/10 bg-white/5 p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Utvalgt kamp</p>
                <h2 className="mt-1 text-xl font-black uppercase tracking-[0.05em]">{matchStageLabel(featuredMatch.stage)}</h2>
              </div>
              <span className="chip bg-mint/10 text-mint">
                <Radio size={14} /> {matchStatusLabel(featuredMatch.status)}
              </span>
            </div>
          </div>
          <div className="space-y-3 p-5">
            <div className="soft-card flex items-center justify-between gap-3 p-3">
              <TeamBadge inverted linked={false} team={featuredMatch.home_team} />
              <strong className="text-2xl">{featuredMatch.home_score ?? "-"}</strong>
            </div>
            <div className="soft-card flex items-center justify-between gap-3 p-3">
              <TeamBadge inverted linked={false} team={featuredMatch.away_team} />
              <strong className="text-2xl">{featuredMatch.away_score ?? "-"}</strong>
            </div>
            <div className="soft-card p-3 text-sm text-white/60">
              <strong className="block text-white">{formatOsloTime(featuredMatch.kickoff_at)}</strong>
              {featuredMatch.stadium}, {featuredMatch.city}
            </div>
            <Link className="primary-action w-full" href={`/matches/${featuredMatch.id}`}>
              Åpne kampdetaljer <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        <LiveTopScorerTable scorers={topScorers} />
        <TopScorerPredictionTable predictions={topScorerPredictions} />
        <TeamLeaderboard teams={teams} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
        <DataFlowStatus status={dataStatus} />
        <div className="dashboard-card">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="eyebrow">Datagrunnlag</p>
              <h2 className="mt-1 text-xl font-black uppercase tracking-[0.05em]">Gratis først, live senere</h2>
            </div>
            <CircleDollarSign className="text-mint" size={24} />
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <div className="soft-card p-4">
              <strong className="block">Seed fallback</strong>
              <p className="mt-2 text-sm leading-6 text-white/60">Appen fungerer uten betalte API-er og viser tydelig når data er demo.</p>
            </div>
            <div className="soft-card p-4">
              <strong className="block">Offisielle lenker</strong>
              <p className="mt-2 text-sm leading-6 text-white/60">NRK og TV 2 lenkes som offisielle sider, uten ulovlige streams.</p>
            </div>
            <div className="soft-card p-4">
              <strong className="block">Live-klar</strong>
              <p className="mt-2 text-sm leading-6 text-white/60">Når backend kobles på, kan tips, toppscorere og sannsynlighet oppdateres live.</p>
            </div>
          </div>
          <p className="mt-5 text-sm text-white/50">Befolkning i seedet modellfelt: {compactNumber(teams.reduce((sum, team) => sum + team.population, 0))} samlet.</p>
        </div>
      </section>
    </div>
  );
}
