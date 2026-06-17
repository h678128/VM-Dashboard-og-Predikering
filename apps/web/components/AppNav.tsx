"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrainCircuit, CalendarDays, ClipboardCheck, Grid2X2, History, Medal, Table2, Trophy, UsersRound, type LucideIcon } from "lucide-react";

const nav: Array<[string, string, LucideIcon]> = [
  ["Oversikt", "/", Grid2X2],
  ["Kamper", "/matches", CalendarDays],
  ["Lag", "/teams", Trophy],
  ["Spillere", "/players", UsersRound],
  ["Tabeller", "/leaderboards", Table2],
  ["Prediksjoner", "/predictions", ClipboardCheck],
  ["Modellverksted", "/model", BrainCircuit],
  ["Historikk", "/historical-insights", History]
];

export function AppNav({ compact = false }: { compact?: boolean }) {
  const pathname = usePathname();

  return (
    <div className={compact ? "grid grid-cols-2 gap-1 px-3 pb-3" : "grid gap-2"}>
      {nav.map(([label, href, Icon]) => {
        const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            className={`focus-ring inline-flex items-center gap-3 rounded-md px-3 py-3 text-sm font-semibold transition ${
              isActive ? "bg-mint text-night" : "text-white/68 hover:bg-white/10 hover:text-white"
            } ${compact ? "justify-center px-2 py-2 text-xs" : ""}`}
            href={href}
          >
            <Icon size={16} />
            {label}
          </Link>
        );
      })}
    </div>
  );
}

export function AppLogo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="inline-flex items-center gap-3">
      <span className={`${compact ? "size-9" : "size-10"} grid place-items-center rounded-md bg-mint text-night shadow-sm shadow-mint/20`}>
        <Medal size={compact ? 18 : 21} />
      </span>
      <span className="leading-tight">
        <span className={`${compact ? "text-base" : "text-lg"} block font-black uppercase tracking-[0.08em]`}>VM 2026</span>
        {!compact ? <span className="block text-[11px] font-medium uppercase tracking-[0.18em] text-white/50">Analysehub</span> : null}
      </span>
    </span>
  );
}
