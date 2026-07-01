import { Trophy } from "lucide-react";
import type { TournamentKnockoutMatch, TournamentSimulation } from "@/lib/types";
import { TeamBadge } from "./TeamBadge";

type KnockoutStage = Exclude<TournamentKnockoutMatch["stage"], "final">;
type FlowDirection = "left" | "right" | "none";

const roundLabels: Record<TournamentKnockoutMatch["stage"], string> = {
  round_of_32: "16-delsfinale",
  round_of_16: "Åttedelsfinale",
  quarterfinal: "Kvartfinale",
  semifinal: "Semifinale",
  final: "Finale"
};

const leftStages: KnockoutStage[] = ["round_of_32", "round_of_16", "quarterfinal", "semifinal"];
const rightStages: KnockoutStage[] = ["semifinal", "quarterfinal", "round_of_16", "round_of_32"];

const sideMatchNumbers: Record<"left" | "right", Record<KnockoutStage, number[]>> = {
  left: {
    round_of_32: [74, 77, 73, 75, 83, 84, 81, 82],
    round_of_16: [89, 90, 93, 94],
    quarterfinal: [97, 98],
    semifinal: [101]
  },
  right: {
    round_of_32: [76, 78, 79, 80, 86, 88, 85, 87],
    round_of_16: [91, 92, 95, 96],
    quarterfinal: [99, 100],
    semifinal: [102]
  }
};

function BracketMatch({
  match,
  flow = "none",
  featured = false
}: {
  match: TournamentKnockoutMatch;
  flow?: FlowDirection;
  featured?: boolean;
}) {
  const homeWon = match.winner_team.id === match.home_team.id;
  const awayWon = match.winner_team.id === match.away_team.id;

  return (
    <div
      className={`relative rounded-md border p-3 text-sm shadow-sm ${
        featured ? "border-mint/50 bg-mint/10 ring-1 ring-mint/20" : "border-ink/10 bg-frost"
      }`}
    >
      {flow !== "none" ? (
        <span
          aria-hidden="true"
          className={`absolute top-1/2 h-px w-3 bg-ink/20 ${flow === "right" ? "-right-3" : "-left-3"}`}
        />
      ) : null}
      <div className="mb-2 flex items-center justify-between text-xs text-ink/45">
        <span>Kamp {match.match_number}</span>
        {match.decided_by === "penalties" ? <span>Etter straffer</span> : null}
      </div>
      <div className={`flex items-center justify-between gap-3 ${homeWon ? "text-pine" : "text-ink/65"}`}>
        <TeamBadge compact linked={false} team={match.home_team} />
        <strong>
          {match.home_score}
          {match.home_penalty_score != null ? ` (${match.home_penalty_score})` : ""}
        </strong>
      </div>
      <div className={`mt-2 flex items-center justify-between gap-3 ${awayWon ? "text-pine" : "text-ink/65"}`}>
        <TeamBadge compact linked={false} team={match.away_team} />
        <strong>
          {match.away_score}
          {match.away_penalty_score != null ? ` (${match.away_penalty_score})` : ""}
        </strong>
      </div>
    </div>
  );
}

function BracketColumn({
  label,
  matches,
  flow
}: {
  label: string;
  matches: TournamentKnockoutMatch[];
  flow: Exclude<FlowDirection, "none">;
}) {
  return (
    <div className="min-w-0">
      <div className="mb-3 border-b border-ink/10 pb-2 text-center">
        <strong className="text-xs uppercase text-ink/55">{label}</strong>
      </div>
      <div className="relative h-[920px]">
        {matches.map((match, index) => (
          <div
            key={match.match_number}
            className="absolute left-0 w-full -translate-y-1/2"
            style={{ top: `${((index + 0.5) / matches.length) * 100}%` }}
          >
            <BracketMatch flow={flow} match={match} />
          </div>
        ))}
      </div>
    </div>
  );
}

export function TournamentBracket({ simulation }: { simulation: TournamentSimulation }) {
  const bracket = simulation.example_bracket;
  const hasBracket = bracket.round_of_32.length > 0;
  const splitRound = (stage: KnockoutStage, side: "left" | "right") => {
    const matchesByNumber = new Map(bracket[stage].map((match) => [match.match_number, match]));
    return sideMatchNumbers[side][stage]
      .map((matchNumber) => matchesByNumber.get(matchNumber))
      .filter((match): match is TournamentKnockoutMatch => match != null);
  };

  return (
    <section className="surface overflow-hidden p-5">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Monte Carlo</p>
          <h2 className="mt-1 text-lg font-semibold">Veien til VM-finalen</h2>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-ink/60">
            Sluttspillet er delt i to halvdeler som møtes i finalen. Dette er én eksempelkjøring gjennom VM-strukturen basert på {simulation.iterations.toLocaleString("nb-NO")} simuleringer.
          </p>
        </div>
        <span className="chip bg-pine/10 text-pine">
          <Trophy size={14} /> {simulation.format.round_of_32_teams} lag
        </span>
      </div>

      {hasBracket ? (
        <div className="overflow-x-auto pb-3">
          <div className="mb-3 grid min-w-[1880px] grid-cols-3 items-center text-center text-xs font-semibold uppercase text-ink/45">
            <span>Venstre halvdel</span>
            <span>Finale</span>
            <span>Høyre halvdel</span>
          </div>
          <div
            className="grid min-w-[1880px] gap-3"
            style={{ gridTemplateColumns: "repeat(4, minmax(190px, 1fr)) minmax(220px, 1.1fr) repeat(4, minmax(190px, 1fr))" }}
          >
            {leftStages.map((stage) => (
              <BracketColumn
                key={`left-${stage}`}
                flow="right"
                label={roundLabels[stage]}
                matches={splitRound(stage, "left")}
              />
            ))}

            <div className="min-w-0">
              <div className="mb-3 border-b border-mint/40 pb-2 text-center">
                <strong className="text-xs uppercase text-pine">{roundLabels.final}</strong>
              </div>
              <div className="relative h-[920px]">
                {bracket.final.map((match) => (
                  <div key={match.match_number} className="absolute left-0 top-1/2 w-full -translate-y-1/2">
                    <div className="mb-3 flex justify-center">
                      <span className="chip bg-mint text-night"><Trophy size={14} /> VM-finale</span>
                    </div>
                    <BracketMatch featured match={match} />
                    <p className="mt-3 text-center text-xs text-ink/50">
                      Vinner: <strong className="text-pine">{match.winner_team.name}</strong>
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {rightStages.map((stage) => (
              <BracketColumn
                key={`right-${stage}`}
                flow="left"
                label={roundLabels[stage]}
                matches={splitRound(stage, "right")}
              />
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
