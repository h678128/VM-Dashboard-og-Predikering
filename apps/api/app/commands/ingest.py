import json
from pathlib import Path

import typer

from app.services.external_data import ExternalSource, configured_sources, fetch_json, write_cache
from app.services.match_import import import_matches_payload
from app.services.seed_data import MATCHES, TEAMS

app = typer.Typer(help="Datainnhenting for VM Dashboard og Predikering.")


def import_source(source_key: str, force: bool = False) -> None:
    source = next((item for item in configured_sources() if item.key == source_key), None)
    if source is None:
        raise typer.BadParameter(f"Ukjent datakilde: {source_key}")
    result = fetch_json(source, force=force)
    typer.echo(f"{source.label}: {result['status']}")
    if result.get("cache_path"):
        typer.echo(f"Raw-cache: {result['cache_path']}")
    if result.get("message"):
        typer.echo(result["message"])


@app.command()
def import_teams(force: bool = typer.Option(False, help="Ignorer fersk cache og hent på nytt.")) -> None:
    import_source("fifa_schedule", force)


@app.command()
def import_players(force: bool = typer.Option(False, help="Ignorer fersk cache og hent på nytt.")) -> None:
    import_source("api_football_live", force)


@app.command()
def import_matches(
    force: bool = typer.Option(False, help="Ignorer fersk cache og hent på nytt."),
    source_file: Path | None = typer.Option(
        None,
        help="Lokal JSON-fil med kamper. Nyttig for gratis/manuelt verifisert snapshot.",
    ),
    source_url: str | None = typer.Option(
        None,
        help="JSON-URL som overstyrer FIFA_SCHEDULE_URL for denne kjøringen.",
    ),
) -> None:
    if source_file:
        payload = json.loads(source_file.read_text(encoding="utf-8"))
        write_cache("fifa_schedule", payload, str(source_file))
        output_path = import_matches_payload(
            payload,
            TEAMS,
            MATCHES,
            source_name=f"Lokal fil: {source_file.name}",
            source_url=str(source_file),
        )
        typer.echo(f"Importerte {len(payload.get('matches', []))} kamper fra lokal fil.")
        typer.echo(f"Processed: {output_path}")
        return

    source = next((item for item in configured_sources() if item.key == "fifa_schedule"), None)
    if source is None:
        raise typer.BadParameter("Ukjent datakilde: fifa_schedule")
    if source_url:
        source = ExternalSource(
            key=source.key,
            label=source.label,
            purpose=source.purpose,
            url=source_url,
            requires_key=source.requires_key,
        )

    result = fetch_json(source, force=force)
    typer.echo(f"{source.label}: {result['status']}")
    if result.get("cache_path"):
        typer.echo(f"Raw-cache: {result['cache_path']}")
    if result.get("message"):
        typer.echo(result["message"])
    payload = result.get("payload")
    if not payload:
        raise typer.Exit(1)

    output_path = import_matches_payload(
        payload,
        TEAMS,
        MATCHES,
        source_name=source.label,
        source_url=source.url,
    )
    typer.echo(f"Processed: {output_path}")


@app.command()
def import_historical_world_cup() -> None:
    typer.echo("Historisk VM-import er klargjort for Fjelstul-datasettet som lokal CSV/JSON.")


@app.command()
def import_country_indicators(force: bool = typer.Option(False, help="Ignorer fersk cache og hent på nytt.")) -> None:
    import_source("world_bank", force)


@app.command()
def import_rankings(force: bool = typer.Option(False, help="Ignorer fersk cache og hent på nytt.")) -> None:
    import_source("fifa_rankings", force)
    import_source("world_football_elo", force)


@app.command()
def import_broadcast_links() -> None:
    typer.echo("Broadcast-lenker valideres mot NRK/TV 2 allowlist i API-et.")


if __name__ == "__main__":
    app()

