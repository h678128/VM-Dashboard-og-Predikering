import { ArrowUpRight, CircleX, ShieldCheck, Trophy } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { MatchCard } from "@/components/MatchCard";
import { PlayerCard } from "@/components/PlayerCard";
import { TeamBadge } from "@/components/TeamBadge";
import { teamName } from "@/lib/labels";
import { getTeamTournamentStatus } from "@/lib/standings";

function formatNumber(value: number | null | undefined): string {
  return typeof value === "number" ? value.toLocaleString("nb-NO") : "Ikke tilgjengelig";
}

export default async function TeamPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const teamId = Number(id);
  const [team, matches] = await Promise.all([api.team(teamId), api.matches()]);
  const teamMatches = matches.filter(
    (match) => match.home_team_id === teamId || match.away_team_id === teamId
  );
  const finishedMatches = teamMatches.filter((match) => match.status === "finished").length;
  const upcomingMatches = teamMatches.filter((match) => match.status === "scheduled").length;
  const tournamentStatus = getTeamTournamentStatus(teamId, matches);
  const StatusIcon = tournamentStatus.kind === "eliminated"
    ? CircleX
    : tournamentStatus.kind === "champion"
      ? Trophy
      : ShieldCheck;
  const statusColors = tournamentStatus.kind === "eliminated"
    ? "border-coral/25 bg-coral/10 text-coral"
    : tournamentStatus.kind === "champion"
      ? "border-gold/30 bg-gold/10 text-gold"
      : "border-mint/25 bg-mint/10 text-pine";
  return (
    <div className="space-y-5">
      <section className="surface p-5 md:p-6">
        <TeamBadge team={team} />
        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          <div className="rounded-md bg-frost p-3 text-sm">FIFA <strong className="block text-xl">{team.fifa_ranking}</strong></div>
          <div className="rounded-md bg-frost p-3 text-sm">Elo <strong className="block text-xl">{team.elo_rating}</strong></div>
          <div className="rounded-md bg-frost p-3 text-sm">Befolkning <strong className="block text-xl">{formatNumber(team.population)}</strong></div>
          <div className="rounded-md bg-frost p-3 text-sm">BNP/cap <strong className="block text-xl">{formatNumber(team.gdp_per_capita)}</strong></div>
        </div>
      </section>
      <section className={`surface border p-5 ${statusColors}`}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3">
            <span className="grid size-11 shrink-0 place-items-center rounded-md bg-white/60">
              <StatusIcon size={22} />
            </span>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.14em] opacity-65">Turneringsstatus</p>
              <h2 className="mt-1 text-xl font-bold text-ink">{tournamentStatus.title}</h2>
              <p className="mt-1 text-sm text-ink/65">{tournamentStatus.detail}</p>
            </div>
          </div>
          {tournamentStatus.match ? (
            <Link className="focus-ring inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2.5 text-sm font-bold text-white transition hover:bg-pine" href={`/matches/${tournamentStatus.match.id}`}>
              {tournamentStatus.opponent ? `Se kampen mot ${teamName(tournamentStatus.opponent)}` : "Se kampen"}
              <ArrowUpRight size={16} />
            </Link>
          ) : null}
        </div>
      </section>
      <section className="surface p-5">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="eyebrow">Terminliste</p>
            <h2 className="mt-1 text-lg font-semibold">Kamper</h2>
            <p className="mt-1 text-sm text-ink/60">
              {finishedMatches} ferdigspilt · {upcomingMatches} kommende
            </p>
          </div>
          <span className="chip bg-frost text-ink/60">{teamMatches.length} registrert</span>
        </div>
        {teamMatches.length ? (
          <div className="grid gap-3 lg:grid-cols-2">
            {teamMatches.map((match) => <MatchCard key={match.id} match={match} />)}
          </div>
        ) : (
          <p className="rounded-md border border-dashed border-ink/20 bg-frost p-4 text-sm text-ink/60">
            Ingen kamper er importert for dette laget ennå.
          </p>
        )}
      </section>
      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {(team.players ?? []).map((player) => <PlayerCard key={player.id} player={player} />)}
      </section>
    </div>
  );
}

