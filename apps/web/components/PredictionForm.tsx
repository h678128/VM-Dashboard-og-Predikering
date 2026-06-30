"use client";

import { useMemo, useState } from "react";
import { Send } from "lucide-react";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "@/lib/config";
import { teamName } from "@/lib/labels";
import type { Match, Player, Team, UserPrediction } from "@/lib/types";

type PredictionFormProps = {
  match?: Match;
  matches?: Match[];
  players: Player[];
  teams: Team[];
};

function formatKickoff(value: string): string {
  return new Intl.DateTimeFormat("nb-NO", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Oslo"
  }).format(new Date(value));
}

function predictionIsOpen(match: Match, currentTime: number): boolean {
  return match.status === "scheduled" && new Date(match.kickoff_at).getTime() > currentTime;
}

export function PredictionForm({ match: initialMatch, matches, players, teams }: PredictionFormProps) {
  const router = useRouter();
  const [currentTime] = useState(() => Date.now());
  const candidateMatches = useMemo(
    () => matches ?? (initialMatch ? [initialMatch] : []),
    [initialMatch, matches]
  );
  const availableMatches = useMemo(
    () => candidateMatches.filter((item) => predictionIsOpen(item, currentTime)),
    [candidateMatches, currentTime]
  );
  const [selectedMatchId, setSelectedMatchId] = useState(availableMatches[0]?.id ?? 0);
  const [homeScore, setHomeScore] = useState("1");
  const [awayScore, setAwayScore] = useState("0");
  const [firstScorer, setFirstScorer] = useState("");
  const [tournamentWinner, setTournamentWinner] = useState(String(teams[0]?.id ?? ""));
  const [topScorer, setTopScorer] = useState(String(players[0]?.id ?? ""));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<UserPrediction | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedMatch = availableMatches.find((item) => item.id === selectedMatchId) ?? availableMatches[0];
  const matchPlayers = useMemo(() => {
    if (!selectedMatch) return [];
    return players.filter(
      (player) => player.team_id === selectedMatch.home_team_id || player.team_id === selectedMatch.away_team_id
    );
  }, [players, selectedMatch]);

  function selectMatch(matchId: number) {
    setSelectedMatchId(matchId);
    setFirstScorer("");
    setResult(null);
    setError(null);
  }

  const homeScoreNumber = Number.parseInt(homeScore, 10);
  const awayScoreNumber = Number.parseInt(awayScore, 10);
  const scoresAreValid = Number.isInteger(homeScoreNumber) && Number.isInteger(awayScoreNumber);
  const predictedWinnerId = !selectedMatch || !scoresAreValid
    ? null
    : homeScoreNumber > awayScoreNumber
      ? selectedMatch.home_team_id
      : awayScoreNumber > homeScoreNumber
        ? selectedMatch.away_team_id
        : null;

  const comparison = useMemo(() => {
    if (!selectedMatch) return null;
    const predictedWinner = predictedWinnerId === selectedMatch.home_team_id
      ? teamName(selectedMatch.home_team)
      : predictedWinnerId === selectedMatch.away_team_id
        ? teamName(selectedMatch.away_team)
        : "Uavgjort";
    return {
      predictedWinner,
      score: `${homeScore}-${awayScore}`,
      modelHint: "Modellens baseline sammenlignes med tipset etter at kampresultatet er verifisert."
    };
  }, [awayScore, homeScore, predictedWinnerId, selectedMatch]);

  async function submitPrediction() {
    if (!selectedMatch || !scoresAreValid) {
      setError("Oppgi et gyldig resultat før tipset sendes.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setResult(null);

    const payload = {
      match_id: selectedMatch.id,
      user_name: "portfolio_guest",
      predicted_home_score: homeScoreNumber,
      predicted_away_score: awayScoreNumber,
      predicted_winner_team_id: predictedWinnerId,
      first_goalscorer_player_id: firstScorer ? Number(firstScorer) : null,
      group_winners_json: null,
      tournament_winner_team_id: tournamentWinner ? Number(tournamentWinner) : null,
      tournament_top_scorer_player_id: topScorer ? Number(topScorer) : null
    };

    try {
      const response = await fetch(`${API_BASE_URL}/predictions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const responseBody = (await response.json()) as UserPrediction | { detail?: string };
      if (!response.ok) {
        const detail = "detail" in responseBody ? responseBody.detail : null;
        throw new Error(detail || "API-et avviste prediksjonen.");
      }
      setResult(responseBody as UserPrediction);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Kunne ikke sende prediksjonen.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!selectedMatch) {
    if (initialMatch) {
      return (
        <section className="surface p-4">
          <p className="eyebrow">Bruker mot modell</p>
          <h2 className="mt-1 text-lg font-semibold">Tipsfristen er stengt</h2>
          <p className="mt-2 text-sm leading-6 text-ink/60">
            Tips måtte sendes før avspark {formatKickoff(initialMatch.kickoff_at)}.
          </p>
        </section>
      );
    }
    return (
      <section className="surface p-4">
        <p className="eyebrow">Bruker mot modell</p>
        <h2 className="mt-1 text-lg font-semibold">Ingen åpne kamper</h2>
        <p className="mt-2 text-sm leading-6 text-ink/60">
          Nye tips kan legges inn når terminlisten inneholder en kommende kamp med åpen tipsfrist.
        </p>
      </section>
    );
  }

  return (
    <section className="surface p-4">
      <div className="mb-4">
        <p className="eyebrow">Bruker mot modell</p>
        <h2 className="text-lg font-semibold">Din prediksjon</h2>
      </div>

      {matches ? (
        <label className="mb-4 block text-sm font-semibold">
          Kamp
          <select
            className="field"
            value={selectedMatch.id}
            onChange={(event) => selectMatch(Number(event.target.value))}
          >
            {availableMatches.map((item) => (
              <option key={item.id} value={item.id}>
                {teamName(item.home_team)} - {teamName(item.away_team)} · {formatKickoff(item.kickoff_at)}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm font-semibold">
          {teamName(selectedMatch.home_team)}
          <input className="field" max="30" min="0" required type="number" value={homeScore} onChange={(event) => setHomeScore(event.target.value)} />
        </label>
        <label className="text-sm font-semibold">
          {teamName(selectedMatch.away_team)}
          <input className="field" max="30" min="0" required type="number" value={awayScore} onChange={(event) => setAwayScore(event.target.value)} />
        </label>
        <label className="text-sm font-semibold">
          Første målscorer
          <select className="field" value={firstScorer} onChange={(event) => setFirstScorer(event.target.value)}>
            <option value="">Ingen valgt</option>
            {matchPlayers.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}
          </select>
        </label>
        <label className="text-sm font-semibold">
          Turneringsvinner
          <select className="field" value={tournamentWinner} onChange={(event) => setTournamentWinner(event.target.value)}>
            {teams.map((team) => <option key={team.id} value={team.id}>{teamName(team)}</option>)}
          </select>
        </label>
        <label className="text-sm font-semibold sm:col-span-2">
          Toppscorer
          <select className="field" value={topScorer} onChange={(event) => setTopScorer(event.target.value)}>
            {players.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}
          </select>
        </label>
      </div>
      {comparison ? (
        <div className="mt-4 rounded-md bg-frost p-3 text-sm">
          <strong>{comparison.score}</strong> - {comparison.predictedWinner}. {comparison.modelHint}
        </div>
      ) : null}
      <button className="primary-action mt-4 w-full disabled:cursor-not-allowed disabled:bg-ink/35" disabled={isSubmitting || !scoresAreValid} type="button" onClick={submitPrediction}>
        <Send size={17} /> {isSubmitting ? "Sender tips..." : "Send tips til API"}
      </button>
      {result ? (
        <div className="mt-3 rounded-md border border-pine/20 bg-pine/10 p-3 text-sm text-ink">
          <strong>Lagret.</strong> Poengene beregnes når kampresultatet er verifisert.
        </div>
      ) : null}
      {error ? (
        <div className="mt-3 rounded-md border border-coral/25 bg-coral/10 p-3 text-sm text-coral">
          {error}
        </div>
      ) : null}
    </section>
  );
}
