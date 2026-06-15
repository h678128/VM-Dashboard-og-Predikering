import { api } from "@/lib/api";
import { matchStageLabel } from "@/lib/labels";
import { BroadcastLinksCard } from "@/components/BroadcastLinksCard";
import { FormationPitch } from "@/components/FormationPitch";
import { ModelExplanationCard } from "@/components/ModelExplanationCard";
import { PredictionForm } from "@/components/PredictionForm";
import { TeamBadge } from "@/components/TeamBadge";
import { WinProbabilityTimeline } from "@/components/WinProbabilityTimeline";

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: rawId } = await params;
  const id = Number(rawId);
  const [match, prediction, live, players, teams] = await Promise.all([
    api.match(id),
    api.prediction(id),
    api.live(id),
    api.players(),
    api.teams()
  ]);

  return (
    <div className="space-y-5">
      <section className="rounded-md border border-ink/10 bg-white/88 p-5">
        <div className="text-sm text-ink/60">{matchStageLabel(match.stage)} - {match.stadium}, {match.city}</div>
        <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          <TeamBadge team={match.home_team} />
          <div className="rounded-sm bg-ink px-5 py-3 text-2xl font-bold text-white">
            {match.home_score ?? "-"} : {match.away_score ?? "-"}
          </div>
          <div className="justify-self-end">
            <TeamBadge team={match.away_team} />
          </div>
        </div>
      </section>
      <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5">
          <ModelExplanationCard prediction={prediction} />
          <WinProbabilityTimeline changes={live.what_changed} timeline={live.timeline} />
          <FormationPitch formation="4-3-3" />
        </div>
        <div className="space-y-5">
          <PredictionForm match={match} players={players} teams={teams} />
          <BroadcastLinksCard broadcasts={match.broadcasts ?? []} />
          <section className="rounded-md border border-ink/10 bg-white/88 p-4">
            <h2 className="mb-3 text-lg font-semibold">xG og kampdata</h2>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="rounded-sm bg-frost p-3">xG hjemme <strong className="block">{live.current.home_xg}</strong></div>
              <div className="rounded-sm bg-frost p-3">xG borte <strong className="block">{live.current.away_xg}</strong></div>
              <div className="rounded-sm bg-frost p-3">Skudd på mål hjemme <strong className="block">{live.current.home_shots_on_target}</strong></div>
              <div className="rounded-sm bg-frost p-3">Skudd på mål borte <strong className="block">{live.current.away_shots_on_target}</strong></div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
