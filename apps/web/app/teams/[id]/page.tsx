import { api } from "@/lib/api";
import { PlayerCard } from "@/components/PlayerCard";
import { TeamBadge } from "@/components/TeamBadge";

function formatNumber(value: number | null | undefined): string {
  return typeof value === "number" ? value.toLocaleString("nb-NO") : "Ikke tilgjengelig";
}

export default async function TeamPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const team = await api.team(Number(id));
  return (
    <div className="space-y-5">
      <section className="rounded-md border border-ink/10 bg-white/88 p-5">
        <TeamBadge team={team} />
        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          <div className="rounded-sm bg-frost p-3">FIFA <strong className="block">{team.fifa_ranking}</strong></div>
          <div className="rounded-sm bg-frost p-3">Elo <strong className="block">{team.elo_rating}</strong></div>
          <div className="rounded-sm bg-frost p-3">Befolkning <strong className="block">{formatNumber(team.population)}</strong></div>
          <div className="rounded-sm bg-frost p-3">BNP/cap <strong className="block">{formatNumber(team.gdp_per_capita)}</strong></div>
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {(team.players ?? []).map((player) => <PlayerCard key={player.id} player={player} />)}
      </section>
    </div>
  );
}

