# VM Dashboard og Predikering

![Tester](https://img.shields.io/badge/tester-pytest-2f6f91)
![Lint](https://img.shields.io/badge/lint-ruff%20%2F%20eslint-d5a021)
![Bygg](https://img.shields.io/badge/bygg-docker%20%2F%20vercel-0f5d4f)

**Live demo:** [https://vm-dashboard-og-predikering.vercel.app](https://vm-dashboard-og-predikering.vercel.app)

VM Dashboard og Predikering er et fullstack dashboard for VM 2026, laget med norske brukere i tankene. Appen samler kampoversikt, tabeller, spillerdata, prediksjoner, modellforklaringer og offisielle norske TV-lenker i én moderne analyseflate.

Alle kamptider vises i `Europe/Oslo`, og sendinger skal bare lenke til offisielle aktører som NRK, NRK TV, TV 2, TV 2 Play, TV 2 Direkte og TV 2 Sport 1. Prosjektet embedder ikke ulovlige streams.

## Status

Frontend er deployet på Vercel og fungerer som offentlig demo. Første versjon bruker et kilde-merket kamp-snapshot i `data/processed/matches.json`, med seed-data som fallback der data mangler. Arkitekturen er samtidig klargjort for ekte datakilder og liveleverandører.

Det betyr at prosjektet i dag demonstrerer produkt, arkitektur og modellflyt med importert gratisdata, mens ekte full live-data krever at API-et kobles til verifiserte kilder som FIFA-resultater, Fjelstul World Cup Database, World Football Elo Ratings, FIFA-rangeringer, World Bank, StatsBomb Open Data eller API-Football.

## Hva appen kan

- Vise terminliste, resultater og gruppetabeller med norsk tid.
- Vise kampdetaljer med score, arena, hendelser, kort, xG, ballbesittelse, formasjon og live vinnsannsynlighet.
- Lenke til offisielle norske broadcaster-sider.
- La brukere tippe resultat, vinner, første målscorer, gruppevinnere, VM-vinner og toppscorer.
- Poengsette tips med reglene: riktig vinner, riktig målforskjell, eksakt score, første målscorer og VM-toppscorer.
- Forklare større endringer i live-sannsynlighet gjennom “Hva endret seg?”.
- Simulere turneringsutfall med Monte Carlo.
- La brukeren velge mellom flere prediksjonsmodeller.

## Modellene

Appen har fire valgbare deterministiske modeller:

| Modell | Versjon | Kort forklart |
| --- | --- | --- |
| Enkel modell | `wc-v0.1-simple` | Kontrollmodell basert på FIFA-rangering og Elo. |
| Landmodell | `wc-v0.2-country-features` | Standardmodell med landnivå-features, økonomiske proxyer, fotballkultur og historisk VM-styrke. |
| Avansert modell | `wc-v0.3-squad-context` | Legger til spillerstyrke, landslagsproduksjon og tidlig turneringsform. |
| Ekspertmodell | `wc-v0.4-many-parameters` | Mange-parameter-modell som er klar for historisk trening og kalibrering senere. |

Modellene bruker ikke tilfeldighet i rå sannsynligheter. Tilfeldighet brukes bare i Monte Carlo-simuleringer. Økonomi, befolkning og fotballpopularitet er proxyer, ikke direkte årsaksforklaringer, og dette er dokumentert i appen og i [docs/model.md](docs/model.md).

## Arkitektur

Prosjektet er et monorepo med tydelig skille mellom frontend, API, datalag og ML-arbeid:

```text
apps/web
  Next.js, TypeScript og Tailwind CSS.
  Viser dashboard, kamper, lag, spillere, prediksjoner og Modellverksted.

apps/api
  FastAPI, Pydantic, SQLAlchemy og Alembic.
  Eksponerer REST-endepunkter, SSE, prediksjoner, simulering og datastatus.

data
  Rådata, prosesserte data og seed-data.

ml
  Struktur for feature engineering, trening, inferens og evaluering.

PostgreSQL + Redis
  Klargjort for lokal utvikling og Render-deploy.
```

Kampdata kan oppdateres gratis med:

```bash
cd apps/api
worldcup-ingest import-matches --source-file ../../data/processed/matches.json
```

Kommandoen kan også bruke en JSON-URL via `--source-url` eller `FIFA_SCHEDULE_URL`, skriver raw-cache til `data/raw` og oppdaterer `data/processed/matches.json`.

Mer detaljert dokumentasjon ligger her:

- [docs/architecture.md](docs/architecture.md)
- [docs/system-overview.md](docs/system-overview.md)
- [docs/model.md](docs/model.md)
- [docs/data-sources.md](docs/data-sources.md)
- [docs/deploy.md](docs/deploy.md)
- [docs/roadmap.md](docs/roadmap.md)

## Teknologi

- Frontend: Next.js, TypeScript, Tailwind CSS og lucide-react.
- Backend: FastAPI, Python og Pydantic.
- Database: PostgreSQL.
- ORM og migrering: SQLAlchemy og Alembic.
- Liveoppdateringer: Server-Sent Events.
- Cache/jobber: Redis er klargjort.
- Tester: pytest for backend-logikk.
- Lint/format: ruff, black og ESLint.
- Lokal drift: Docker Compose.

## Kom i gang lokalt

Start backend:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

API-dokumentasjon: [http://localhost:8000/docs](http://localhost:8000/docs)

Start frontend:

```bash
cd apps/web
npm install
npm run dev
```

Appen kjører på [http://localhost:3000](http://localhost:3000).

Du kan også starte hele stacken med Docker Compose:

```bash
docker compose up --build
```

Standardverdiene i Compose er bare lokale eksempelverdier. Bruk egne secrets og deploy-spesifikke porter før prosjektet settes i et delt miljø.

## Nyttige kommandoer

Backend:

```bash
cd apps/api
pytest
ruff check .
alembic upgrade head
worldcup-ingest import-teams
worldcup-ingest import-broadcast-links
```

Frontend:

```bash
cd apps/web
npm run lint
npm run build
npm audit --audit-level=moderate
```

## API-eksempel

`GET /matches/1/prediction?model_id=country`

```json
{
  "match_id": 1,
  "model_id": "country",
  "model_name": "Landmodell",
  "model_version": "wc-v0.2-country-features",
  "home_win_probability": 0.47,
  "draw_probability": 0.27,
  "away_win_probability": 0.26,
  "expected_home_goals": 1.34,
  "expected_away_goals": 1.02,
  "predicted_score": "1-1"
}
```

`GET /matches/1/live-probability`

```json
{
  "current": { "minute": 64, "home_score": 1, "away_score": 0 },
  "what_changed": [
    {
      "event_type": "goal",
      "minute": 24,
      "score_state": "1-0",
      "probability_delta": 0.21
    }
  ]
}
```

## Deploy

Prosjektet er satt opp for:

- Frontend på Vercel fra `apps/web`.
- API på Render fra `apps/api`.
- PostgreSQL og Redis på Render via `render.yaml`.

Se [docs/deploy.md](docs/deploy.md) for miljøvariabler og stegvis deploy-oppsett.

## Roadmap

- [ ] Flytte seedet datalag over til PostgreSQL-repositories.
- [ ] Koble på provider-adaptere med caching, råresponslagring og rate-limit-håndtering.
- [ ] Legge til ekte live-data for kamper, hendelser, tabeller og toppscorere.
- [ ] Utvide historisk backtesting på FIFA/Fjelstul-data.
- [ ] Implementere faktiske grafer for kalibrering, forvekslingsmatrise og SHAP-lignende forklaringer.
- [ ] Legge til autentisering og persistente bruker-ligaer.
- [ ] Sette opp CI for backend-tester, frontend-lint og Docker-build.
