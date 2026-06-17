import Image from "next/image";
import Link from "next/link";
import { teamName } from "@/lib/labels";
import type { Team } from "@/lib/types";

type TeamBadgeProps = {
  team: Team;
  compact?: boolean;
  linked?: boolean;
  inverted?: boolean;
};

export function TeamBadge({ team, compact = false, linked = true, inverted = false }: TeamBadgeProps) {
  const codeClassName = inverted ? "text-xs text-white/60" : "text-xs text-white/50";
  const content = (
    <>
      {team.flag_url ? (
        <Image
          alt=""
          className="shrink-0 rounded-sm object-cover shadow-sm"
          height={compact ? 18 : 24}
          src={team.flag_url}
          width={compact ? 26 : 34}
        />
      ) : null}
      <span className={compact ? "truncate text-sm font-semibold leading-tight" : "truncate font-semibold leading-tight"}>{teamName(team)}</span>
      <span className={`shrink-0 ${codeClassName}`}>{team.fifa_code}</span>
    </>
  );

  if (!linked) {
    return <span className="inline-flex min-w-0 max-w-full items-center gap-2 overflow-hidden rounded-md px-1 py-1">{content}</span>;
  }

  return (
    <Link className="focus-ring inline-flex min-w-0 max-w-full items-center gap-2 overflow-hidden rounded-md px-1 py-1 transition hover:bg-white/10" href={`/teams/${team.id}`}>
      {content}
    </Link>
  );
}
