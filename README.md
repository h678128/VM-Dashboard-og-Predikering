# VM Dashboard og Predikering

![Tester](https://img.shields.io/badge/tester-pytest-2f6f91)
![Lint](https://img.shields.io/badge/lint-ruff%20%2F%20eslint-d5a021)
![Bygg](https://img.shields.io/badge/bygg-docker%20%2F%20vercel-0f5d4f)

Et fullstack VM-prosjekt for kampoversikt, prediksjoner, historisk innsikt og modellforklaringer. Løsningen er laget med norske brukere i tankene: kamptidspunkt vises i `Europe/Oslo`, og sendinger lenkes bare til offisielle norske aktører som NRK, NRK TV, TV 2, TV 2 Play, TV 2 Direkte og TV 2 Sport 1.

Første versjon kjører på seedet/mock-data, slik at prosjektet fungerer uten betalte API-er. Arkitekturen er samtidig klargjort for ekte datakilder som FIFA-resultater, Fjelstul World Cup Database, World Football Elo Ratings, FIFA-rangeringer, World Bank, StatsBomb Open Data og live-leverandører som API-Football.

## Deploy

Prosjektet har ekte deploy-oppsett for:

- Frontend på Vercel fra `apps/web`
- API på Render fra `apps/api`
- PostgreSQL og Redis på Render via `render.yaml`

Se [docs/deploy.md](docs/deploy.md) for trinnvis oppsett, miljøvariabler og kontrollkommandoer.

## Skjermbilder

- `docs/screenshots/home.png` kommer
- `docs/screenshots/match-detail.png` kommer
- `docs/screenshots/model-lab.png` kommer

## Hva prosjektet viser

- Fullstack monorepo med Next.js, FastAPI, SQLAlchemy og Alembic.
- TypeScript-frontend med dashboardsider, kampsider, prediksjonsskjema og Model Lab.
- FastAPI-backend med dokumenterte endepunkter, seed-data, simulering og live-sannsynlighet.
- Datamodell for lag, spillere, kamper, hendelser, lagoppstillinger, sendinger, brukerprediksjoner, modellprediksjoner og sannsynlighetshendelser.
- Modelllogikk som skiller mellom deterministiske sannsynligheter og tilfeldighet i Monte Carlo-simuleringer.
- Norsk produktfokus: Oslo-tid, offisielle norske TV-lenker og ingen ulovlige streams.
- Deploy-hensyn: produksjons-Dockerfile, CORS-konfigurasjon, lokale demo-secrets, rate-/input-grenser og auditert frontend-avhengighetstre.

## Arkitektur

```text
apps/web (Next.js)
  -> Henter data fra API-et med seedet fallback
  -> Viser kamper, lag, spillere, prediksjoner, Model Lab og historiske innsikter

apps/api (FastAPI)
  -> REST-endepunkter og SSE-endepunkt for liveoppdateringer
  -> SQLAlchemy-modeller og Alembic-migrering
  -> Seedet datalag for første versjon
  -> Tjenester for prediksjoner, live-sannsynlighet og turneringssimulering

ml/
  -> Mapper for feature engineering, trening, inferens og evaluering

data/
  -> Rådata, prosesserte data og seed-data

PostgreSQL + Redis
  -> Klargjort i docker-compose for lokal utvikling og Render for deploy
```

Se også:

- [docs/architecture.md](docs/architecture.md)
- [docs/system-overview.md](docs/system-overview.md)
- [docs/model.md](docs/model.md)
- [docs/data-sources.md](docs/data-sources.md)
- [docs/roadmap.md](docs/roadmap.md)

## Funksjoner

- Kampoversikt og resultater med tidspunkter i `Europe/Oslo`.
- Kampdetaljer med score, arena, xG, hendelser, lagoppstillinger, formasjon og live vinnsannsynlighet.
- Offisielle norske sendelenker for NRK og TV 2.
- Bruker mot modell: tipp resultat, vinner, første målscorer, gruppevinnere, VM-vinner og toppscorer.
- Poengberegning for prediksjoner:
  - Riktig vinner: 3 poeng
  - Riktig målforskjell: 2 poeng
  - Eksakt resultat: 5 poeng
  - Riktig første målscorer: 4 poeng
  - Riktig VM-toppscorer: 10 poeng
- "Hva endret seg?"-forklaringer når live-sannsynlighet flytter seg betydelig.
- Støtte for formasjonene `4-3-3`, `4-2-3-1`, `3-4-3`, `3-5-2`, `5-3-2` og `4-4-2`.
- Turneringssimulator for avansement, utslagsrunder, semifinale, finale og VM-seier.
- Model Lab med versjonshistorikk, feature importance, backtesting-metrikker og plassholdere for kalibrering, confusion matrix og SHAP.
- Seed-data for Norge, Frankrike, Senegal, Irak, Nederland, Spania, Portugal og Brasil.

## Teknologi

- Frontend: Next.js, TypeScript, Tailwind CSS, lucide-react og Recharts-klare komponenter.
- Backend: FastAPI, Python og Pydantic.
- Database: PostgreSQL.
- ORM og migrering: SQLAlchemy og Alembic.
- ML: deterministisk Python-baseline, med struktur for pandas, scikit-learn, XGBoost eller LightGBM senere.
- Liveoppdateringer: Server-Sent Events fra FastAPI.
- Bakgrunnsjobber/cache: Redis er klargjort.
- Tester: pytest for backend-logikk.
- Lint/format: ruff/black og ESLint.
- Lokal drift: Docker Compose.

## Kom i gang lokalt

Backend:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

API-dokumentasjon: [http://localhost:8000/docs](http://localhost:8000/docs)

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

App: [http://localhost:3000](http://localhost:3000)

Docker Compose:

```bash
docker compose up --build
```

Standardverdiene i Compose er bare lokale demo-verdier. PostgreSQL og Redis bindes til `127.0.0.1` som standard. Bruk egne secrets og deploy-spesifikke porter før prosjektet settes i et delt miljø.

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

## Eksempel på API-respons

`GET /matches/1/prediction`

```json
{
  "match_id": 1,
  "model_version": "wc-v0.2-norway",
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

## Modell

Modellversjon `wc-v0.2-norway` er en deterministisk baseline. Den bruker normaliserte features som FIFA-rangering, Elo-rating, BNP per innbygger, befolkning, fotballpopularitet, konføderasjonsstyrke, vertsnasjonseffekt og historisk VM-prestasjon.

BNP, befolkning og fotballpopularitet er grove proxyer, ikke direkte årsaksforklaringer. Det er dokumentert som en begrensning i modellnotatene. Tilfeldighet brukes bare i Monte Carlo-simuleringer, ikke i rå modellprediksjoner.

## Datakilder som er planlagt

- FIFA offisiell terminliste og resultater
- Fjelstul World Cup Database
- international_results
- World Football Elo Ratings
- FIFA-rangeringer
- World Bank BNP per innbygger og befolkning
- StatsBomb Open Data
- API-Football eller tilsvarende liveleverandør
- Offisielle NRK- og TV 2-sider

Første versjon bruker seed-data og mockede live snapshots. Prosjektet embedder ikke og lenker ikke til ulovlige streams.

## Roadmap

- [ ] Flytte seedet datalag over til PostgreSQL-repositories.
- [ ] Lage provider-adaptere med caching, råresponslagring og rate-limit-håndtering.
- [ ] Legge til WebSocket-fanout i tillegg til SSE.
- [ ] Utvide historisk backtesting på FIFA/Fjelstul-data.
- [ ] Implementere faktiske grafer for kalibrering, confusion matrix og SHAP-lignende forklaringer.
- [ ] Legge til autentisering og persistente bruker-ligaer.
- [ ] Sette opp CI for backend-tester, frontend-lint og Docker-build.
