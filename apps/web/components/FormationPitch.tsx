import { teamName } from "@/lib/labels";
import type { Lineup, Match } from "@/lib/types";

const formations: Record<string, number[]> = {
  "4-3-3": [1, 4, 3, 3],
  "4-2-3-1": [1, 4, 2, 3, 1],
  "3-4-3": [1, 3, 4, 3],
  "3-5-2": [1, 3, 5, 2],
  "5-3-2": [1, 5, 3, 2],
  "4-4-2": [1, 4, 4, 2]
};

function FormationRows({ formation }: { formation: string }) {
  const rows = formations[formation];
  if (!rows) {
    return (
      <div className="grid min-h-[220px] place-items-center rounded-md bg-white/10 p-4 text-center text-sm font-semibold text-white">
        Formasjonen {formation} er ikke støttet i visningen ennå.
      </div>
    );
  }

  return (
    <div className="relative grid min-h-[320px] gap-3 rounded-lg border border-white/60 bg-[linear-gradient(135deg,#0f5d4f,#2f6f91)] p-4 shadow-inner">
      <div className="pointer-events-none absolute inset-4 rounded-md border border-white/40" />
      <div className="pointer-events-none absolute left-4 right-4 top-1/2 border-t border-white/35" />
      {rows.map((count, rowIndex) => (
        <div key={`${formation}-${rowIndex}`} className="relative z-10 flex items-center justify-around gap-2">
          {Array.from({ length: count }).map((_, index) => (
            <div key={index} className="grid h-9 w-9 place-items-center rounded-full bg-white text-sm font-bold text-pine shadow">
              {rowIndex === 0 ? "GK" : index + 1}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export function FormationPitch({ match, lineups }: { match: Match; lineups: Lineup[] }) {
  const confirmedLineups = lineups.filter((lineup) => lineup.formation);
  const teamsById = new Map([
    [match.home_team_id, match.home_team],
    [match.away_team_id, match.away_team]
  ]);

  return (
    <section className="surface p-4">
      <div className="mb-4">
        <p className="eyebrow">Taktikk</p>
        <h2 className="text-lg font-semibold">Formasjon</h2>
        <p className="mt-1 text-sm text-ink/60">
          Viser bare bekreftede lagoppstillinger fra kampdata. Ingen hardkodet standardformasjon.
        </p>
      </div>

      {confirmedLineups.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {confirmedLineups.map((lineup) => {
            const team = teamsById.get(lineup.team_id);
            return (
              <div key={lineup.id} className="space-y-3">
                <div className="flex items-center justify-between gap-3 rounded-md bg-frost px-3 py-2 text-sm">
                  <span className="font-semibold">{team ? teamName(team) : `Lag ${lineup.team_id}`}</span>
                  <strong>{lineup.formation}</strong>
                </div>
                <FormationRows formation={lineup.formation} />
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-md bg-frost p-4 text-sm leading-6 text-ink/65">
          Formasjon er ikke bekreftet for denne kampen ennå. Når offisiell startellever eller live lineup-data finnes, vises riktig formasjon her.
        </div>
      )}
    </section>
  );
}
