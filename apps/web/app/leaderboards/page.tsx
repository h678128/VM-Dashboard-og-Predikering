import { GroupStandingsTable, LiveTopScorerTable, PlayerProfileTable, TopScorerPredictionTable } from "@/components/Leaderboards";
import { DataProvenance } from "@/components/DataProvenance";
import { TournamentBracket } from "@/components/TournamentBracket";
import { api } from "@/lib/api";

export default async function LeaderboardsPage() {
  const [players, topScorers, topScorerPredictions, groupStandings, dataStatus, tournament] = await Promise.all([
    api.players(),
    api.topScorers(),
    api.topScorerPredictions(),
    api.groupStandings(),
    api.dataStatus(),
    api.tournament()
  ]);

  return (
    <div className="space-y-5">
      <section className="surface p-5 md:p-6">
        <p className="eyebrow">Oversikt</p>
        <h1 className="mt-1 text-3xl font-bold">Tabeller</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/60">
          Alle grupper vises. Poeng beregnes bare fra registrerte, bekreftede kampdata.
        </p>
        <div className="mt-5 border-t border-white/10 pt-4">
          <DataProvenance compact status={dataStatus} />
        </div>
      </section>

      <GroupStandingsTable groups={groupStandings} />

      <TournamentBracket simulation={tournament} />

      <div className="grid gap-4 lg:grid-cols-2">
        <LiveTopScorerTable scorers={topScorers} />
        <TopScorerPredictionTable predictions={topScorerPredictions} />
        <PlayerProfileTable players={players} />
      </div>
    </div>
  );
}
