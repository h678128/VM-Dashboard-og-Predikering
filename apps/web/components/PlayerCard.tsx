import type { Player } from "@/lib/types";

export function PlayerCard({ player }: { player: Player }) {
  return (
    <div className="surface p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-ink/50">#{player.shirt_number} - {player.position}</div>
          <h2 className="mt-1 text-xl font-bold">{player.name}</h2>
          <p className="mt-1 text-sm text-ink/60">{player.club}</p>
        </div>
        <span className="rounded-md bg-ink px-2 py-1 text-sm font-bold text-white">{player.rating}</span>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
        <div className="rounded-md bg-frost p-3"><span className="block text-ink/50">Kamper</span><strong>{player.caps}</strong></div>
        <div className="rounded-md bg-frost p-3"><span className="block text-ink/50">Mål</span><strong>{player.goals}</strong></div>
        <div className="rounded-md bg-frost p-3"><span className="block text-ink/50">Alder</span><strong>{player.age}</strong></div>
      </div>
    </div>
  );
}
