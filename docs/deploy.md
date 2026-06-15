# Deploy

Dette prosjektet er klargjort for en enkel offentlig demo med:

- Vercel for frontend i `apps/web`
- Render for API i `apps/api`
- Render PostgreSQL og Redis via `render.yaml`

## 1. Deploy backend på Render

1. Gå til Render og velg **New Blueprint**.
2. Koble til GitHub-repoet `h678128/VM-Dashboard-og-Predikering`.
3. Render leser `render.yaml` fra rotmappen.
4. Opprett tjenestene:
   - `vm-dashboard-api`
   - `vm-dashboard-db`
   - `vm-dashboard-redis`
5. Sett `ALLOWED_ORIGINS` når du kjenner frontend-URL-en.

Eksempel:

```text
https://vm-dashboard-og-predikering.vercel.app
```

API-et har health check her:

```text
https://<render-api-url>/health
```

## 2. Deploy frontend på Vercel

1. Importer GitHub-repoet i Vercel.
2. Sett **Root Directory** til:

```text
apps/web
```

3. Vercel bruker `apps/web/vercel.json`.
4. Sett miljøvariabel:

```text
NEXT_PUBLIC_API_BASE_URL=https://<render-api-url>
```

5. Deploy.

## 3. Oppdater CORS i Render

Når Vercel-URL-en er klar, gå tilbake til Render og sett:

```text
ALLOWED_ORIGINS=https://<vercel-url>
```

Hvis du vil støtte både lokal utvikling og deploy:

```text
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://<vercel-url>
```

## 4. Lokal kontroll før deploy

Backend:

```bash
cd apps/api
python -m pytest tests
python -m ruff check app tests
```

Frontend:

```bash
cd apps/web
npm run lint
npm run build
npm audit --audit-level=moderate
```

Docker Compose:

```bash
docker compose config
```

## Viktig

- Ikke legg ekte secrets i repoet.
- `.env` er ignorert.
- `.env.example` inneholder bare lokale demo-verdier.
- Postgres og Redis i `docker-compose.yml` er bundet til `127.0.0.1` som standard.
- Frontend bruker seed fallback hvis API-et ikke svarer, men deploy bør settes opp med `NEXT_PUBLIC_API_BASE_URL`.
