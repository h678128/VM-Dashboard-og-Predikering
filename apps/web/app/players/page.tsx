import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { TeamBadge } from "@/components/TeamBadge";

export default async function PlayersPage() {
  const [players, teams] = await Promise.all([api.players(), api.teams()]);
  const teamById = new Map(teams.map((team) => [team.id, team]));
  const rankedPlayers = [...players].sort((first, second) => (second.rating ?? 0) - (first.rating ?? 0));

  return (
    <div className="space-y-5">
      <section className="surface p-5 md:p-6">
        <p className="eyebrow">Spillerbase</p>
        <h1 className="mt-1 text-3xl font-black uppercase tracking-[0.05em]">Spillere</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/60">
          Landskamper og landslagsmål viser spillerens totale landslagsstatistikk. VM 2026-mål beregnes separat fra registrerte kamphendelser i turneringen.
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {rankedPlayers.map((player) => {
          const team = teamById.get(player.team_id);
          return (
            <Link
              key={player.id}
              className="focus-ring group block rounded-lg border border-white/10 bg-card p-5 text-white transition hover:-translate-y-0.5 hover:border-mint/40 hover:bg-white/10"
              href={`/players/${player.id}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-white/50">#{player.shirt_number} · {player.position}</div>
                  <h2 className="mt-1 truncate text-xl font-bold">{player.name}</h2>
                  <p className="mt-1 truncate text-sm text-white/60">{player.club}</p>
                </div>
                <span className="rounded-md bg-mint/10 px-2 py-1 text-sm font-black text-mint">{player.rating}</span>
              </div>

              <div className="mt-4 flex items-center justify-between gap-3">
                {team ? <TeamBadge compact inverted linked={false} team={team} /> : <span className="text-sm text-white/50">Ukjent lag</span>}
                <ArrowRight className="text-white/35 transition group-hover:translate-x-1 group-hover:text-mint" size={18} />
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                <div className="rounded-md bg-white/10 p-3"><span className="block text-white/50">Landskamper</span><strong>{player.caps}</strong></div>
                <div className="rounded-md bg-white/10 p-3"><span className="block text-white/50">Landslagsmål</span><strong>{player.goals}</strong></div>
                <div className="rounded-md bg-white/10 p-3"><span className="block text-white/50">VM 2026-mål</span><strong>{player.tournament_goals}</strong></div>
                <div className="rounded-md bg-white/10 p-3"><span className="block text-white/50">Alder</span><strong>{player.age}</strong></div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
