import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { TeamBadge } from "@/components/TeamBadge";

export default async function TeamsPage() {
  const teams = await api.teams();
  const orderedTeams = [...teams].sort(
    (first, second) =>
      (first.group_name ?? "").localeCompare(second.group_name ?? "") ||
      first.fifa_ranking - second.fifa_ranking ||
      first.name.localeCompare(second.name)
  );
  return (
    <div className="space-y-5">
      <section className="surface p-5 md:p-6">
        <p className="eyebrow">Land og modellfeatures</p>
        <h1 className="mt-1 text-3xl font-bold">Lag</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/60">
          Komplett seedet lagfelt for alle grupper med FIFA-rangering, Elo og enkle landnivåvariabler for prediksjonsmodellen.
        </p>
      </section>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {orderedTeams.map((team) => (
          <Link key={team.id} className="focus-ring group block rounded-lg border border-ink/10 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-fjord/35 hover:shadow-[0_18px_48px_rgba(23,33,31,0.11)]" href={`/teams/${team.id}`}>
            <div className="flex items-start justify-between gap-3">
              <TeamBadge linked={false} team={team} />
              <div className="flex items-center gap-2">
                {team.group_name ? <span className="chip bg-frost text-ink/65">Gruppe {team.group_name}</span> : null}
                <ArrowRight className="text-ink/35 transition group-hover:translate-x-1 group-hover:text-pine" size={18} />
              </div>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-2 text-sm">
              <div className="rounded-md bg-frost p-3">
                <span className="block text-ink/50">FIFA</span>
                <strong>{team.fifa_ranking}</strong>
              </div>
              <div className="rounded-md bg-frost p-3">
                <span className="block text-ink/50">Elo</span>
                <strong>{team.elo_rating}</strong>
              </div>
              <div className="rounded-md bg-frost p-3">
                <span className="block text-ink/50">Region</span>
                <strong>{team.confederation}</strong>
              </div>
              <div className="rounded-md bg-frost p-3">
                <span className="block text-ink/50">Fotball</span>
                <strong>{Math.round(team.football_popularity_score * 100)}%</strong>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
