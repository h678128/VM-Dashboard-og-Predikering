import { ClipboardCheck } from "lucide-react";
import { api } from "@/lib/api";
import { teamName } from "@/lib/labels";
import { PredictionForm } from "@/components/PredictionForm";

export default async function PredictionsPage() {
  const [matches, players, teams, predictions] = await Promise.all([
    api.matches(),
    api.players(),
    api.teams(),
    api.predictions()
  ]);

  const teamsById = new Map(teams.map((team) => [team.id, team]));
  const latestPredictions = predictions.slice(-5).reverse();
  const scheduledMatches = matches.filter((match) => match.status === "scheduled");

  return (
    <div className="space-y-5">
      <section className="surface p-5 md:p-6">
        <div className="flex items-start gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-md bg-fjord/10 text-fjord">
            <ClipboardCheck size={22} />
          </span>
          <div>
            <p className="eyebrow">Tipskonkurranse</p>
            <h1 className="mt-1 text-3xl font-bold">Bruker vs modell</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/60">
              Velg en kommende kamp og legg inn resultat, første målscorer og turneringsvalg. Tipsfristen stenger ved avspark.
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <PredictionForm matches={scheduledMatches} players={players} teams={teams} />
        <section className="surface p-4">
          <div className="mb-4">
            <p className="eyebrow">Regler</p>
            <h2 className="text-lg font-semibold">Poengsystem</h2>
          </div>
          <div className="grid gap-2 text-sm sm:grid-cols-2">
            {[
              ["Vinner", 3],
              ["Målforskjell", 2],
              ["Eksakt resultat", 5],
              ["Første målscorer", 4],
              ["Turnerings-toppscorer", 10]
            ].map(([label, points]) => (
              <div key={String(label)} className="rounded-md bg-frost p-3">
                <span>{label}</span>
                <strong className="block">{points} p</strong>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="surface p-4">
        <div className="mb-4">
          <p className="eyebrow">API</p>
          <h2 className="text-lg font-semibold">Siste tips</h2>
        </div>
        {latestPredictions.length ? (
          <div className="space-y-2">
            {latestPredictions.map((prediction) => {
              const winner = prediction.predicted_winner_team_id
                ? teamsById.get(prediction.predicted_winner_team_id)
                : null;
              return (
                <div key={prediction.id} className="grid gap-2 rounded-md bg-frost p-3 text-sm sm:grid-cols-[1fr_auto]">
                  <span>
                    {prediction.predicted_home_score}-{prediction.predicted_away_score} - {winner ? teamName(winner) : "Uavgjort"}
                  </span>
                  <strong>{prediction.scoring ? `${prediction.points} poeng` : "Venter på resultat"}</strong>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-ink/60">Ingen tips er lagret ennå.</p>
        )}
      </section>
    </div>
  );
}
