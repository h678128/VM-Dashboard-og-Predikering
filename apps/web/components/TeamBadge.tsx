import Image from "next/image";
import Link from "next/link";
import type { Team } from "@/lib/types";

type TeamBadgeProps = {
  team: Team;
  compact?: boolean;
  linked?: boolean;
};

export function TeamBadge({ team, compact = false, linked = true }: TeamBadgeProps) {
  const content = (
    <>
      {team.flag_url ? (
        <Image
          alt=""
          className="rounded-sm object-cover"
          height={compact ? 18 : 24}
          src={team.flag_url}
          width={compact ? 26 : 34}
        />
      ) : null}
      <span className={compact ? "text-sm font-semibold" : "font-semibold"}>{team.name}</span>
      <span className="text-xs text-ink/55">{team.fifa_code}</span>
    </>
  );

  if (!linked) {
    return <span className="inline-flex items-center gap-2 rounded-md px-1 py-1">{content}</span>;
  }

  return (
    <Link className="focus-ring inline-flex items-center gap-2 rounded-md px-1 py-1" href={`/teams/${team.id}`}>
      {content}
    </Link>
  );
}
