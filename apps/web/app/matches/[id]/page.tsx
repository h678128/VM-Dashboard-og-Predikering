import { Activity, MapPin } from "lucide-react";
import { api, formatOsloTime } from "@/lib/api";
import { matchStageLabel, matchStatusLabel } from "@/lib/labels";
import { BroadcastLinksCard } from "@/components/BroadcastLinksCard";
import { FormationPitch } from "@/components/FormationPitch";
import { MatchEventTimeline } from "@/components/MatchEventTimeline";
import { ModelExplanationCard } from "@/components/ModelExplanationCard";
import { PredictionForm } from "@/components/PredictionForm";
import { PossessionComparison } from "@/components/PossessionComparison";
import { TeamBadge } from "@/components/TeamBadge";
import { WinProbabilityTimeline } from "@/components/WinProbabilityTimeline";

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: rawId } = await params;
  const id = Number(rawId);
  const [match, events, prediction, live, lineups, players, teams] = await Promise.all([
    api.match(id),
    api.matchEvents(id),
    api.prediction(id),
    api.live(id),
    api.lineups(id),
    api.players(),
    api.teams()
  ]);
  const hasLiveData = live.timeline.length > 0;
  const liveStat = (value: number | undefined) => hasLiveData ? value ?? 0 : "Ikke startet";

  return (
    <div className="space-y-5">
      <section className="surface overflow-hidden">
        <div className="border-b border-ink/10 bg-ink px-5 py-4 text-white md:px-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-white/60">
                {matchStageLabel(match.stage)}{match.group_name ? ` - Gruppe ${match.group_name}` : ""}
              </p>
              <div className="mt-2 flex items-center gap-2 text-sm text-white/70">
                <MapPin size={16} /> {match.stadium}, {match.city}
              </div>
            </div>
            <span className="rounded-md bg-white/10 px-3 py-2 text-sm font-bold">{matchStatusLabel(match.status)}</span>
          </div>
        </div>
        <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 p-5 md:p-6">
          <TeamBadge team={match.home_team} />
          <div className="rounded-md bg-ink px-5 py-3 text-2xl font-bold text-white shadow-sm">
            {match.home_score ?? "-"} : {match.away_score ?? "-"}
          </div>
          <div className="justify-self-end text-right">
            <TeamBadge team={match.away_team} />
          </div>
        </div>
        <div className="border-t border-ink/10 bg-frost px-5 py-3 text-sm text-ink/65 md:px-6">
          {formatOsloTime(match.kickoff_at)} - Europe/Oslo
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5">
          <MatchEventTimeline events={events} match={match} />
          <ModelExplanationCard prediction={prediction} />
          <WinProbabilityTimeline changes={live.what_changed} timeline={live.timeline} />
          <FormationPitch lineups={lineups} match={match} />
        </div>
        <div className="space-y-5">
          <PredictionForm match={match} players={players} teams={teams} />
          <BroadcastLinksCard broadcasts={match.broadcasts ?? []} />
          <section className="surface p-4">
            <div className="mb-3 flex items-center gap-3">
              <span className="grid size-10 place-items-center rounded-md bg-fjord/10 text-fjord">
                <Activity size={20} />
              </span>
              <div>
                <p className="eyebrow">Live</p>
                <h2 className="text-lg font-semibold">xG og kampdata</h2>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <PossessionComparison
                awayPossession={live.current.away_possession}
                homePossession={live.current.home_possession}
                match={match}
              />
              <div className="rounded-md bg-frost p-3">xG hjemme <strong className="block">{liveStat(live.current.home_xg)}</strong></div>
              <div className="rounded-md bg-frost p-3">xG borte <strong className="block">{liveStat(live.current.away_xg)}</strong></div>
              <div className="rounded-md bg-frost p-3">Skudd på mål hjemme <strong className="block">{liveStat(live.current.home_shots_on_target)}</strong></div>
              <div className="rounded-md bg-frost p-3">Skudd på mål borte <strong className="block">{liveStat(live.current.away_shots_on_target)}</strong></div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
