import type { Player, Team, TopScorerPrediction, TopScorerStanding } from "@/lib/types";
import { TeamBadge } from "./TeamBadge";

export function PlayerProfileTable({ players }: { players: Player[] }) {
  const rankedPlayers = [...players]
    .sort((first, second) => (second.rating ?? 0) - (first.rating ?? 0))
    .slice(0, 8);

  return (
    <section className="surface p-5">
      <div className="mb-4">
        <p className="eyebrow">Seed-data</p>
        <h2 className="text-lg font-semibold">Spillerprofiler</h2>
        <p className="mt-1 text-sm text-ink/60">Demo-rangering, ikke ekte VM-toppscorerliste.</p>
      </div>
      <div className="space-y-2">
        {rankedPlayers.map((player, index) => (
          <div key={player.id} className="grid grid-cols-[34px_minmax(0,1fr)_64px] items-center gap-3 rounded-md bg-frost px-3 py-2 text-sm">
            <span className="grid size-7 place-items-center rounded-sm bg-mint/10 font-bold text-mint shadow-sm">{index + 1}</span>
            <span className="truncate font-medium">{player.name}</span>
            <strong className="text-right">{player.rating}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

export function TeamLeaderboard({ teams }: { teams: Team[] }) {
  return (
    <section className="surface p-5">
      <div className="mb-4">
        <p className="eyebrow">Modellfelt</p>
        <h2 className="text-lg font-semibold">Lagstyrke</h2>
      </div>
      <div className="space-y-2">
        {teams.slice(0, 8).map((team) => (
          <div key={team.id} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-md bg-frost px-3 py-2 text-sm">
            <TeamBadge compact team={team} />
            <div className="text-right text-white">
              <span className="block text-xs text-ink/50">FIFA {team.fifa_ranking}</span>
              <strong>{team.elo_rating}</strong>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function LiveTopScorerTable({ scorers }: { scorers: TopScorerStanding[] }) {
  return (
    <section className="surface p-5">
      <div className="mb-4">
        <p className="eyebrow">Live data</p>
        <h2 className="text-lg font-semibold">Toppscorere</h2>
        <p className="mt-1 text-sm text-ink/60">Teller kun mål som finnes i registrerte kamphendelser.</p>
      </div>
      {scorers.length ? (
        <div className="space-y-2">
          {scorers.slice(0, 8).map((item, index) => (
            <div key={item.player_id} className="grid grid-cols-[34px_minmax(0,1fr)_58px] items-center gap-3 rounded-md bg-frost px-3 py-2 text-sm">
              <span className="grid size-7 place-items-center rounded-sm bg-mint/10 font-bold text-mint shadow-sm">{index + 1}</span>
              <span className="min-w-0">
                <span className="block truncate font-medium">{item.player.name}</span>
                <span className="text-xs text-ink/50">{item.team?.fifa_code ?? "Ukjent lag"}</span>
              </span>
              <strong className="text-right">{item.goals} mål</strong>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-dashed border-white/20 bg-white/10 p-4 text-sm leading-6 text-white/60">
          Ingen mål er registrert i kampdata ennå. Når live-/resultatdata kobles på, oppdateres listen her.
        </div>
      )}
    </section>
  );
}

export function TopScorerPredictionTable({ predictions }: { predictions: TopScorerPrediction[] }) {
  return (
    <section className="surface p-5">
      <div className="mb-4">
        <p className="eyebrow">Modell</p>
        <h2 className="text-lg font-semibold">Predikert toppscorer</h2>
        <p className="mt-1 text-sm text-ink/60">Forecast basert på spiller-rating, målrate og lagstyrke.</p>
      </div>
      <div className="space-y-3">
        {predictions.slice(0, 8).map((item, index) => {
          const probability = Math.round(item.probability * 100);
          return (
            <div key={item.player_id} className="space-y-1">
              <div className="grid grid-cols-[34px_minmax(0,1fr)_52px] items-center gap-3 text-sm">
                <span className="grid size-7 place-items-center rounded-sm bg-mint/10 font-bold text-mint">{index + 1}</span>
                <span className="min-w-0">
                  <span className="block truncate font-medium">{item.player.name}</span>
                  <span className="text-xs text-ink/50">{item.team.fifa_code} - {item.expected_goals} forv. mål</span>
                </span>
                <strong className="text-right">{probability}%</strong>
              </div>
              <div className="ml-[46px] h-2 rounded-sm bg-white/10">
                <div className="h-2 rounded-sm bg-mint" style={{ width: `${Math.max(probability, 2)}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
