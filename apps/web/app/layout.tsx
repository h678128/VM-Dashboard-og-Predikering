import type { Metadata } from "next";
import Link from "next/link";
import { BarChart3 } from "lucide-react";
import "./globals.css";
import { APP_NAME } from "@/lib/labels";

export const metadata: Metadata = {
  title: APP_NAME,
  description: "Norsk VM-dashboard for prediksjoner, kamper og modellinnsikt"
};

const nav = [
  ["Kamper", "/matches"],
  ["Lag", "/teams"],
  ["Tabeller", "/leaderboards"],
  ["Prediksjoner", "/predictions"],
  ["Modellverksted", "/model"],
  ["Historikk", "/historical-insights"]
];

function NavLinks({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? "flex gap-1 overflow-x-auto px-4 pb-3" : "grid gap-1"}>
      {nav.map(([label, href]) => (
        <Link key={href} className="focus-ring rounded-md px-3 py-2 text-sm font-semibold text-ink/68 transition hover:bg-frost hover:text-ink" href={href}>
          {label}
        </Link>
      ))}
    </div>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nb">
      <body>
        <div className="min-h-screen lg:grid lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className="hidden border-r border-ink/10 bg-white/82 px-4 py-5 backdrop-blur lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col">
            <Link className="focus-ring flex items-center gap-3 rounded-md p-2 font-bold text-ink" href="/">
              <span className="grid size-10 place-items-center rounded-md bg-pine text-white shadow-sm">
                <BarChart3 size={20} />
              </span>
              <span className="leading-tight">{APP_NAME}</span>
            </Link>
            <nav className="mt-6">
              <NavLinks />
            </nav>
            <div className="mt-auto rounded-lg border border-ink/10 bg-frost p-3 text-sm text-ink/65">
              <strong className="block text-ink">Gratis portfolio-demo</strong>
              Seed-data, norsk tid og offisielle TV-lenker.
            </div>
          </aside>

          <div className="min-w-0">
            <header className="sticky top-0 z-40 border-b border-ink/10 bg-white/95 backdrop-blur lg:hidden">
              <div className="flex items-center gap-3 px-4 py-3">
                <Link className="focus-ring mr-auto inline-flex items-center gap-2 rounded-md font-bold text-ink" href="/">
                  <span className="grid size-9 place-items-center rounded-md bg-pine text-white">
                    <BarChart3 size={18} />
                  </span>
                  {APP_NAME}
                </Link>
              </div>
              <NavLinks compact />
            </header>
            <main className="mx-auto max-w-7xl px-4 py-5 md:px-6 md:py-7 lg:px-8">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
