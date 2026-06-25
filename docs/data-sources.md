# Datakilder

Første versjon leveres med `data/processed/matches.json` som kilde-merket kamp-snapshot, og seed-data som fallback der importerte data mangler.

## Klargjort for live-API

Backend er strukturert for ekte dataleverandører, men krever dem ikke for offentlig visning.

- `GET /data/sources` viser hvilke eksterne kilder som er konfigurert og om råcache finnes.
- `GET /data/status` viser om API-et bruker importert processed-data, seedet visning eller konfigurerte eksterne kilder.
- `GET /live/ticker` gir frontend ett samlet payload til live-tickeren øverst.
- `worldcup-ingest import-matches` kan hente `FIFA_SCHEDULE_URL` og skrive rårespons til `data/raw`.
- `worldcup-ingest import-rankings` kan hente `FIFA_RANKINGS_URL` og `WORLD_FOOTBALL_ELO_URL`.
- `worldcup-ingest import-country-indicators` kan bruke konfigurert World Bank-base-URL.
- `worldcup-ingest import-players` er reservert for en liveleverandør som API-Football.

Konfigurerte leverandørresponser caches før normalisering. Hvis en leverandør feiler, kan API-et fortsatt servere importert processed-data, seedet visning eller siste cachede payload.

## Oppdatere kampdata gratis

Kampimporten kan bruke en URL fra `FIFA_SCHEDULE_URL`, en midlertidig `--source-url`, eller en lokal JSON-fil med gratis/manuelt verifiserte resultater.

```bash
worldcup-ingest import-matches --source-file data/processed/matches.json
worldcup-ingest import-matches --source-url https://example.com/world-cup-matches.json
```

Importen skriver original payload til `data/raw/fifa_schedule/latest.json` og normalisert appdata til `data/processed/matches.json`. Frontend og API bruker deretter processed-data før seed fallback.

## Miljøvariabler

| Variabel | Bruk |
| --- | --- |
| `LIVE_DATA_PROVIDER` | `seeded` for seedet visning, eller leverandørnavn som `api-football`. |
| `FIFA_SCHEDULE_URL` | JSON-endepunkt for offisiell terminliste/resultatimport. |
| `FIFA_RANKINGS_URL` | JSON-endepunkt for FIFA-ranking. |
| `WORLD_FOOTBALL_ELO_URL` | JSON-endepunkt eller fil-URL for Elo-import. |
| `WORLD_BANK_BASE_URL` | World Bank API-base. Standard: `https://api.worldbank.org/v2`. |
| `API_FOOTBALL_BASE_URL` | Endepunkt for live fotball-leverandør. |
| `API_FOOTBALL_KEY` | Valgfri leverandørnøkkel. Skal bare ligge i Render eller lokal `.env`, aldri i git. |
| `EXTERNAL_DATA_CACHE_DIR` | Mappe for rårespons-cache. |
| `EXTERNAL_DATA_CACHE_TTL_SECONDS` | Cache-TTL før import forsøker ny leverandørhenting. |

## Planlagte kilder

| Kilde | Bruk | Notater |
| --- | --- | --- |
| FIFA offisiell terminliste/resultater | Kamper, arenaer og resultater | Bruk offisielle ID-er når de finnes. |
| Fjelstul World Cup Database | Historiske VM-data | Nyttig for backtesting og historiske innsikter. |
| international_results | Bredere landslagshistorikk | Nyttig for form og kalibrering. |
| World Football Elo Ratings | Lagstyrke | Importer snapshots per dato. |
| FIFA-rangeringer | Rangering og rankingpoeng | Lagre rankingdato. |
| World Bank | BNP per innbygger og befolkning | Normaliser innen turneringsfeltet. |
| StatsBomb Open Data | Hendelser og xG-eksempler | Åpen dekning er begrenset. |
| API-Football eller lignende | Livehendelser og statistikk | Må caches, rate-begrenses og lagre råpayload. |
| NRK / TV 2-sider | Norske sendinger | Lenke bare til offisielle sider. |

## Datateknikk

- Cache eksterne API-responser.
- Lagre råresponser i `data/raw` eller objektlagring.
- Respekter leverandørenes rate limits.
- Støtt seedet/mock live-modus.
- Gjør polling-intervall konfigurerbart.
- Send oppdateringer til frontend via SSE eller WebSocket.
- Hold leverandørspesifikk kode bak adaptere.

