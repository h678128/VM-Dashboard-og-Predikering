import { History, Timer } from "lucide-react";
import { api } from "@/lib/api";

export default async function HistoricalInsightsPage() {
  const insights = await api.historical();
  const commonScorelines = Array.isArray(insights.common_scorelines) ? insights.common_scorelines : [];
  const goalTiming = Array.isArray(insights.goal_timing_patterns) ? insights.goal_timing_patterns : [];
  return (
    <div className="space-y-5">
      <section className="surface p-5 md:p-6">
        <div className="flex items-start gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-md bg-fjord/10 text-fjord">
            <History size={22} />
          </span>
          <div>
            <p className="eyebrow">VM-data</p>
            <h1 className="mt-1 text-3xl font-bold">Historiske innsikter</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/60">
              Historiske mønstre for kampstatus, comebacks, underdogs og målprofil. Første versjon bruker seedede innsikter.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="metric-tile">Scorer først <strong className="block text-3xl">{Math.round(Number(insights.winning_after_scoring_first ?? 0) * 100)}%</strong></div>
        <div className="metric-tile">Leder til pause <strong className="block text-3xl">{Math.round(Number(insights.winning_when_leading_at_halftime ?? 0) * 100)}%</strong></div>
        <div className="metric-tile">Underdog-seier <strong className="block text-3xl">{Math.round(Number(insights.underdog_win_frequency ?? 0) * 100)}%</strong></div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="surface p-4">
          <div className="mb-4 flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-md bg-pine/10 text-pine">
              <Timer size={20} />
            </span>
            <div>
              <p className="eyebrow">Mønster</p>
              <h2 className="text-lg font-semibold">Måltidspunkt</h2>
            </div>
          </div>
          {goalTiming.map((item: any) => (
            <div key={item.window} className="grid grid-cols-[80px_1fr_52px] items-center gap-2 py-2 text-sm">
              <span>{item.window}</span>
              <div className="h-2 rounded-sm bg-ink/10">
                <div className="h-2 rounded-sm bg-pine" style={{ width: `${Math.min(item.share * 100 * 3, 100)}%` }} />
              </div>
              <strong>{Math.round(item.share * 100)}%</strong>
            </div>
          ))}
        </div>
        <div className="surface p-4">
          <div className="mb-4">
            <p className="eyebrow">Resultat</p>
            <h2 className="text-lg font-semibold">Vanlige resultater</h2>
          </div>
          {commonScorelines.map((item: any) => (
            <div key={item.scoreline} className="flex justify-between border-b border-ink/10 py-2 text-sm last:border-b-0">
              <span>{item.scoreline}</span>
              <strong>{Math.round(item.share * 100)}%</strong>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
