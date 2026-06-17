import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { Activity } from "lucide-react";
import "./globals.css";
import { AppLogo, AppNav } from "@/components/AppNav";
import { LiveTicker } from "@/components/LiveTicker";
import { APP_NAME } from "@/lib/labels";

export const metadata: Metadata = {
  title: APP_NAME,
  description: "Norsk VM-dashboard for prediksjoner, kamper og modellinnsikt"
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nb">
      <body>
        <div className="min-h-screen lg:grid lg:grid-cols-[256px_minmax(0,1fr)]">
          <aside className="hidden border-r border-white/10 bg-night px-3 py-5 text-white lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col">
            <Link className="focus-ring flex items-center gap-3 rounded-md p-2 font-bold" href="/">
              <AppLogo />
            </Link>
            <nav className="mt-7">
              <AppNav />
            </nav>
            <div className="mt-auto rounded-lg border border-white/10 bg-card p-4 text-sm text-white/60">
              <div className="mb-2 flex items-center gap-2 font-bold text-white">
                <Activity className="text-mint" size={16} /> Liveklar demo
              </div>
              Norsk tid, offisielle TV-lenker og seed fallback uten betalte API-er.
            </div>
          </aside>

          <div className="min-w-0">
            <LiveTicker />
            <header className="sticky top-8 z-40 border-b border-white/10 bg-night/96 text-white shadow-sm backdrop-blur lg:hidden">
              <div className="flex items-center gap-3 px-4 py-3">
                <Link className="focus-ring mr-auto inline-flex items-center gap-2 rounded-md font-bold" href="/">
                  <AppLogo compact />
                </Link>
              </div>
              <AppNav compact />
            </header>
            <main className="mx-auto max-w-[1540px] px-4 py-5 md:px-8 md:py-8 lg:px-10">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
