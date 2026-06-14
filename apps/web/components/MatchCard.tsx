import { Radio, Trophy } from "lucide-react";
import Link from "next/link";
import { formatOsloTime } from "@/lib/api";
import type { Match } from "@/lib/types";
import { TeamBadge } from "./TeamBadge";

export function MatchCard({ match }: { match: Match }) {
  return (
    <Link
      className="focus-ring block rounded-md border border-ink/10 bg-white/88 p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
      href={`/matches/${match.id}`}
    >
      <div className="mb-4 flex items-center justify-between gap-3 text-sm text-ink/65">
        <span>
          {match.stage}
          {match.group_name ? ` - Gruppe ${match.group_name}` : ""}
        </span>
        <span className="inline-flex items-center gap-1">
          {match.status === "live" ? <Radio size={15} /> : <Trophy size={15} />} {match.status}
        </span>
      </div>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <TeamBadge linked={false} team={match.home_team} />
        <div className="rounded-sm bg-ink px-3 py-2 text-center font-bold text-white">
          {match.home_score ?? "-"} : {match.away_score ?? "-"}
        </div>
        <div className="justify-self-end">
          <TeamBadge linked={false} team={match.away_team} />
        </div>
      </div>
      <div className="mt-4 text-sm text-ink/70">
        {formatOsloTime(match.kickoff_at)} - {match.city}
      </div>
    </Link>
  );
}
