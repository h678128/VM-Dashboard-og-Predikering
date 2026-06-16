import { Activity, ArrowRight, BarChart3, CalendarDays, Radio, ShieldCheck, Trophy, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { api, formatOsloTime } from "@/lib/api";
import { APP_NAME, matchStageLabel, matchStatusLabel, teamName } from "@/lib/labels";
import { DataFlowStatus } from "@/components/DataFlowStatus";
import { MatchCard } from "@/components/MatchCard";
import { TeamBadge } from "@/components/TeamBadge";
import { TeamLeaderboard, TopScorerTable } from "@/components/Leaderboards";

export default async function HomePage() {
  const [matches, teams, players, tournament, dataStatus] = await Promise.all([
    api.matches(),
    api.teams(),
    api.players(),
    api.tournament(),
    api.dataStatus()
  ]);

  const liveMatch = matches.find((match) => match.status === "live") ?? null;
  const featuredMatch = liveMatch ?? matches[0];
  const upcomingMatches = matches.filter((match) => match.id !== featuredMatch.id).slice(0, 3);
  const tournamentTeams = Array.isArray(tournament.teams) ? tournament.teams.slice(0, 5) : [];
  const officialBroadcasts = matches.reduce((count, match) => count + (match.broadcasts?.length ?? 0), 0);

  const stats: Array<[string, string | number, string, LucideIcon]> = [
    ["Kamper", matches.length, "Terminliste", CalendarDays],
    ["Lag", teams.length, "Seedet felt", BarChart3],
    ["TV-lenker", officialBroadcasts, "Offisielle", ShieldCheck],
    ["Direkte", liveMatch ? "1 kamp" : "Ingen", "SSE klar", Activity]
  ];

  return (
    <div className="space-y-6">
      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="eyebrow">Norsk VM-dashboard</p>
              <h1 className="mt-2 max-w-3xl text-4xl font-bold tracking-normal md:text-5xl">{APP_NAME}</h1>
              <p className="mt-3 max-w-2xl text-base leading-7 text-ink/66">
                Kamper, prediksjoner, modellforklaringer og offisielle norske sendelenker samlet i en ryddig portfolio-demo.
              </p>
            </div>
            <div className="flex gap-2">
              <Link className="primary-action" href="/matches">
                Kamper <ArrowRight size={16} />
              </Link>
              <Link className="secondary-action" href="/model">
                Modell
              </Link>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map(([label, value, helper, Icon]) => (
              <div key={label} className="metric-tile">
                <div className="flex items-center justify-between gap-3">
                  <span className="grid size-9 place-items-center rounded-md bg-frost text-fjord">
                    <Icon size={18} />
                  </span>
                  <span className="text-xs font-bold uppercase tracking-[0.12em] text-ink/40">{helper}</span>
                </div>
                <div className="mt-3 text-sm font-semibold text-ink/55">{label}</div>
                <strong className="text-3xl text-ink">{value}</strong>
              </div>
            ))}
          </div>
        </div>

        <aside className="panel p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="eyebrow">Neste kamp</p>
              <h2 className="mt-1 text-xl font-bold">{matchStageLabel(featuredMatch.stage)}</h2>
            </div>
            <span className="inline-flex items-center gap-1 rounded-md bg-frost px-2 py-1 text-xs font-bold text-fjord">
              <Radio size={14} /> {matchStatusLabel(featuredMatch.status)}
            </span>
          </div>
          <div className="mt-5 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
            <TeamBadge linked={false} team={featuredMatch.home_team} />
            <div className="rounded-md bg-ink px-3 py-2 text-center font-bold text-white">
              {featuredMatch.home_score ?? "-"} : {featuredMatch.away_score ?? "-"}
            </div>
            <div className="justify-self-end text-right">
              <TeamBadge linked={false} team={featuredMatch.away_team} />
            </div>
          </div>
          <div className="mt-5 rounded-md bg-frost p-3 text-sm text-ink/68">
            <strong className="block text-ink">{formatOsloTime(featuredMatch.kickoff_at)}</strong>
            {featuredMatch.stadium}, {featuredMatch.city}
          </div>
          <Link className="mt-4 inline-flex items-center gap-2 text-sm font-bold text-fjord hover:text-pine" href={`/matches/${featuredMatch.id}`}>
            Åpne kampdetaljer <ArrowRight size={15} />
          </Link>
        </aside>
      </section>

      <DataFlowStatus status={dataStatus} />

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-3">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="eyebrow">Terminliste</p>
              <h2 className="mt-1 text-2xl font-bold">Kampoversikt</h2>
              <p className="text-sm text-ink/60">Alle tider vises i norsk tid. Resultater vises først når ekte data finnes.</p>
            </div>
            <Link className="secondary-action" href="/matches">
              Alle kamper <ArrowRight size={16} />
            </Link>
          </div>
          <div className="grid gap-3 lg:grid-cols-3">
            {upcomingMatches.map((match) => <MatchCard key={match.id} match={match} />)}
          </div>
        </div>

        <div className="panel p-4">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <p className="eyebrow">Simulering</p>
              <h2 className="text-lg font-semibold">VM-vinner</h2>
            </div>
            <Trophy className="text-gold" size={22} />
          </div>
          <div className="space-y-3">
            {tournamentTeams.map((item: any) => {
              const winnerProbability = Math.round(item.winner * 100);
              return (
                <div key={item.team_id} className="space-y-1">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="font-medium">{teamName(item.team)}</span>
                    <strong>{winnerProbability}%</strong>
                  </div>
                  <div className="h-2 rounded-sm bg-ink/10">
                    <div className="h-2 rounded-sm bg-pine" style={{ width: `${Math.max(winnerProbability, 2)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="mt-4 text-sm text-ink/60">Basert på seedet modellfelt og Monte Carlo-simuleringer.</p>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <TopScorerTable players={players} />
        <TeamLeaderboard teams={teams} />
      </section>
    </div>
  );
}
