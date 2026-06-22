import { Gauge } from "lucide-react";
import { teamName } from "@/lib/labels";
import type { Match } from "@/lib/types";

function asPercent(value: number): number {
  const percentage = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, percentage));
}

export function PossessionComparison({
  homePossession,
  awayPossession,
  match
}: {
  homePossession?: number | null;
  awayPossession?: number | null;
  match: Match;
}) {
  const hasData = homePossession != null && awayPossession != null;
  const home = hasData ? asPercent(homePossession) : 0;
  const away = hasData ? asPercent(awayPossession) : 0;
  const total = home + away;
  const homeWidth = total > 0 ? (home / total) * 100 : 50;
  const awayWidth = 100 - homeWidth;

  return (
    <div className="col-span-2 rounded-md border border-white/10 bg-frost p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="inline-flex items-center gap-2 font-semibold">
          <Gauge className="text-fjord" size={18} /> Ballbesittelse
        </span>
        {!hasData ? <span className="text-xs font-semibold text-ink/50">Ikke tilgjengelig</span> : null}
      </div>

      {hasData ? (
        <div className="mt-4">
          <div className="flex items-end justify-between gap-4">
            <div>
              <strong className="block text-2xl">{Math.round(home)}%</strong>
              <span className="text-xs text-ink/50">{teamName(match.home_team)}</span>
            </div>
            <div className="text-right">
              <strong className="block text-2xl">{Math.round(away)}%</strong>
              <span className="text-xs text-ink/50">{teamName(match.away_team)}</span>
            </div>
          </div>
          <div className="mt-3 flex h-2.5 overflow-hidden rounded-sm bg-white/10">
            <div className="bg-mint transition-[width]" style={{ width: `${homeWidth}%` }} />
            <div className="bg-fjord transition-[width]" style={{ width: `${awayWidth}%` }} />
          </div>
        </div>
      ) : (
        <p className="mt-3 text-sm leading-6 text-ink/60">
          Vises når en bekreftet kampstatistikk-feed leverer ballbesittelse.
        </p>
      )}
    </div>
  );
}
