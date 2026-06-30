import { Trophy } from "lucide-react";
import type { TournamentKnockoutMatch, TournamentSimulation } from "@/lib/types";
import { TeamBadge } from "./TeamBadge";

const rounds: Array<{
  key: TournamentKnockoutMatch["stage"];
  label: string;
}> = [
  { key: "round_of_32", label: "Runde 32" },
  { key: "round_of_16", label: "Åttedelsfinale" },
  { key: "quarterfinal", label: "Kvartfinale" },
  { key: "semifinal", label: "Semifinale" },
  { key: "final", label: "Finale" }
];

function BracketMatch({ match }: { match: TournamentKnockoutMatch }) {
  const homeWon = match.winner_team.id === match.home_team.id;
  const awayWon = match.winner_team.id === match.away_team.id;

  return (
    <div className="rounded-md border border-ink/10 bg-frost p-3 text-sm shadow-sm">
      <div className="mb-2 flex items-center justify-between text-xs text-ink/45">
        <span>Kamp {match.match_number}</span>
        {match.decided_by === "penalties" ? <span>Etter straffer</span> : null}
      </div>
      <div className={`flex items-center justify-between gap-3 ${homeWon ? "text-pine" : "text-ink/65"}`}>
        <TeamBadge compact linked={false} team={match.home_team} />
        <strong>{match.home_score}</strong>
      </div>
      <div className={`mt-2 flex items-center justify-between gap-3 ${awayWon ? "text-pine" : "text-ink/65"}`}>
        <TeamBadge compact linked={false} team={match.away_team} />
        <strong>{match.away_score}</strong>
      </div>
    </div>
  );
}

export function TournamentBracket({ simulation }: { simulation: TournamentSimulation }) {
  const hasBracket = simulation.example_bracket.round_of_32.length > 0;

  return (
    <section className="surface overflow-hidden p-5">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Monte Carlo</p>
          <h2 className="mt-1 text-lg font-semibold">Simulert utslagsbrakett</h2>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-ink/60">
            Én eksempelkjøring gjennom den offisielle VM-strukturen. Sannsynlighetene beregnes over {simulation.iterations.toLocaleString("nb-NO")} simuleringer.
          </p>
        </div>
        <span className="chip bg-pine/10 text-pine">
          <Trophy size={14} /> {simulation.format.round_of_32_teams} lag
        </span>
      </div>

      {hasBracket ? (
        <div className="overflow-x-auto pb-3">
          <div className="grid min-w-[1280px] grid-cols-5 items-start gap-4">
            {rounds.map((round) => (
              <div key={round.key} className="space-y-3">
                <div className="sticky top-0 z-10 border-b border-ink/10 bg-white/95 pb-2 backdrop-blur">
                  <strong className="text-sm">{round.label}</strong>
                  <span className="ml-2 text-xs text-ink/45">{simulation.example_bracket[round.key].length} kamper</span>
                </div>
                {simulation.example_bracket[round.key].map((match) => (
                  <BracketMatch key={match.match_number} match={match} />
                ))}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-md border border-dashed border-ink/20 bg-frost p-4 text-sm text-ink/60">
          Braketten vises når simulator-API-et er koblet til frontend.
        </div>
      )}
    </section>
  );
}
