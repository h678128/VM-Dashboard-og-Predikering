import { CalendarDays, Radio } from "lucide-react";
import { api, formatOsloTime } from "@/lib/api";
import { matchStatusLabel, teamName } from "@/lib/labels";

export async function LiveTicker() {
  const matches = await api.matches();
  const liveMatches = matches.filter((match) => match.status === "live");
  const featured = liveMatches.length ? liveMatches : matches.slice(0, 5);

  const items = [
    ...featured.map((match) => {
      const score = match.status === "scheduled" ? "ikke startet" : `${match.home_score ?? 0}-${match.away_score ?? 0}`;
      return `${teamName(match.home_team)} - ${teamName(match.away_team)} · ${score} · ${formatOsloTime(match.kickoff_at)} · ${matchStatusLabel(match.status)}`;
    }),
    "Alle tider vises i Europe/Oslo",
    "Kun offisielle norske TV-lenker: NRK, NRK TV, TV 2 og TV 2 Play",
    "Prediksjoner og modellforklaringer oppdateres når live-data er koblet på"
  ];

  const tickerItems = [...items, ...items];

  return (
    <div className="live-ticker" aria-label="Live VM-oppdateringer">
      <div className="live-ticker-label">
        {liveMatches.length ? <Radio size={14} /> : <CalendarDays size={14} />}
        {liveMatches.length ? "Direkte" : "VM live"}
      </div>
      <div className="live-ticker-scroll">
        <div className="live-ticker-track">
          {tickerItems.map((item, index) => (
            <span key={`${item}-${index}`} className="live-ticker-item">
              {index % items.length === 0 ? <span className="live-dot" /> : null}
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
