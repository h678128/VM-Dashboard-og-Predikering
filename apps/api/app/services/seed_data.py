from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def team(
    item_id: int,
    group_name: str,
    name: str,
    code: str,
    confederation: str,
    flag_code: str,
    ranking: int,
    points: float,
    elo: int,
    gdp: int,
    population: int,
    popularity: float,
    history: float,
) -> dict:
    return {
        "id": item_id,
        "group_name": group_name,
        "name": name,
        "fifa_code": code,
        "confederation": confederation,
        "flag_url": f"https://flagcdn.com/{flag_code}.svg",
        "fifa_ranking": ranking,
        "fifa_ranking_points": points,
        "elo_rating": elo,
        "gdp_per_capita": gdp,
        "population": population,
        "football_popularity_score": popularity,
        "host_advantage_score": 0.0,
        "historical_world_cup_score": history,
    }


def player(
    item_id: int,
    team_id: int,
    name: str,
    position: str,
    shirt: int,
    age: int,
    club: str,
    caps: int,
    goals: int,
    rating: int,
) -> dict:
    return {
        "id": item_id,
        "team_id": team_id,
        "name": name,
        "position": position,
        "shirt_number": shirt,
        "age": age,
        "club": club,
        "caps": caps,
        "goals": goals,
        "rating": rating,
    }


def match(
    item_id: int,
    group: str,
    home: int,
    away: int,
    kickoff: str,
    stadium: str,
    city: str,
    status: str = "scheduled",
    home_score: int | None = None,
    away_score: int | None = None,
) -> dict:
    return {
        "id": item_id,
        "tournament_year": 2026,
        "stage": "Group stage",
        "group_name": group,
        "home_team_id": home,
        "away_team_id": away,
        "kickoff_at": utc(kickoff),
        "stadium": stadium,
        "city": city,
        "status": status,
        "home_score": home_score,
        "away_score": away_score,
    }


def event(
    item_id: int,
    match_id: int,
    team_id: int,
    player_id: int | None,
    minute: int,
    description: str,
    extra_minute: int | None = None,
) -> dict:
    return {
        "id": item_id,
        "match_id": match_id,
        "team_id": team_id,
        "player_id": player_id,
        "event_type": "goal",
        "minute": minute,
        "extra_minute": extra_minute,
        "description": description,
    }


TEAMS = [
    team(1, "I", "Norway", "NOR", "UEFA", "no", 29, 1528.0, 1810, 87962, 5_500_000, 0.76, 0.18),
    team(2, "I", "France", "FRA", "UEFA", "fr", 3, 1838.0, 2048, 44461, 68_000_000, 0.92, 0.92),
    team(3, "I", "Senegal", "SEN", "CAF", "sn", 19, 1609.0, 1802, 1598, 17_700_000, 0.88, 0.34),
    team(4, "I", "Iraq", "IRQ", "AFC", "iq", 58, 1410.3, 1640, 5937, 45_500_000, 0.84, 0.08),
    team(5, "J", "Argentina", "ARG", "CONMEBOL", "ar", 2, 1860.0, 2108, 13730, 46_000_000, 0.97, 1.0),
    team(6, "J", "Algeria", "ALG", "CAF", "dz", 35, 1512.0, 1735, 5260, 46_000_000, 0.9, 0.3),
    team(7, "J", "Austria", "AUT", "UEFA", "at", 24, 1546.0, 1815, 56000, 9_100_000, 0.82, 0.42),
    team(8, "J", "Jordan", "JOR", "AFC", "jo", 66, 1375.0, 1555, 4311, 11_500_000, 0.77, 0.02),
    team(9, "K", "Portugal", "POR", "UEFA", "pt", 6, 1748.1, 1975, 27405, 10_400_000, 0.95, 0.62),
    team(10, "K", "DR Congo", "COD", "CAF", "cd", 56, 1420.0, 1648, 715, 105_000_000, 0.86, 0.08),
    team(11, "K", "Uzbekistan", "UZB", "AFC", "uz", 50, 1455.0, 1662, 2496, 36_400_000, 0.72, 0.02),
    team(12, "K", "Colombia", "COL", "CONMEBOL", "co", 13, 1685.0, 1905, 6979, 52_000_000, 0.94, 0.45),
    team(13, "L", "England", "ENG", "UEFA", "gb-eng", 4, 1813.0, 2030, 48900, 57_000_000, 0.96, 0.84),
    team(14, "L", "Croatia", "CRO", "UEFA", "hr", 10, 1710.0, 1900, 21460, 3_900_000, 0.91, 0.82),
    team(15, "L", "Ghana", "GHA", "CAF", "gh", 72, 1350.0, 1610, 2238, 34_000_000, 0.89, 0.34),
    team(16, "L", "Panama", "PAN", "CONCACAF", "pa", 30, 1525.0, 1665, 18490, 4_500_000, 0.74, 0.08),
    team(17, "A", "Mexico", "MEX", "CONCACAF", "mx", 14, 1650.0, 1845, 13926, 129_000_000, 0.94, 0.66),
    team(18, "A", "South Africa", "RSA", "CAF", "za", 60, 1402.0, 1618, 6766, 62_000_000, 0.82, 0.2),
    team(19, "A", "South Korea", "KOR", "AFC", "kr", 25, 1563.0, 1788, 33147, 51_700_000, 0.8, 0.46),
    team(20, "A", "Czech Republic", "CZE", "UEFA", "cz", 40, 1495.0, 1762, 30427, 10_900_000, 0.78, 0.42),
    team(21, "B", "Canada", "CAN", "CONCACAF", "ca", 27, 1548.0, 1745, 53372, 40_800_000, 0.66, 0.1),
    team(22, "B", "Bosnia and Herzegovina", "BIH", "UEFA", "ba", 71, 1358.0, 1588, 7567, 3_200_000, 0.83, 0.08),
    team(23, "B", "Qatar", "QAT", "AFC", "qa", 51, 1447.0, 1668, 87480, 2_700_000, 0.7, 0.08),
    team(24, "B", "Switzerland", "SUI", "UEFA", "ch", 17, 1617.0, 1878, 99995, 8_900_000, 0.78, 0.52),
    team(25, "C", "Brazil", "BRA", "CONMEBOL", "br", 5, 1772.0, 2022, 10044, 203_000_000, 0.98, 1.0),
    team(26, "C", "Morocco", "MAR", "CAF", "ma", 12, 1690.0, 1888, 3850, 37_800_000, 0.92, 0.58),
    team(27, "C", "Haiti", "HAI", "CONCACAF", "ht", 84, 1284.0, 1495, 1748, 11_700_000, 0.76, 0.04),
    team(28, "C", "Scotland", "SCO", "UEFA", "gb-sct", 36, 1510.0, 1738, 49300, 5_500_000, 0.84, 0.28),
    team(29, "D", "United States", "USA", "CONCACAF", "us", 14, 1652.0, 1828, 81632, 336_000_000, 0.68, 0.42),
    team(30, "D", "Paraguay", "PAR", "CONMEBOL", "py", 39, 1501.0, 1748, 6153, 6_100_000, 0.9, 0.36),
    team(31, "D", "Australia", "AUS", "AFC", "au", 26, 1558.0, 1765, 64820, 26_600_000, 0.7, 0.3),
    team(32, "D", "Turkey", "TUR", "UEFA", "tr", 25, 1560.0, 1782, 12985, 85_300_000, 0.9, 0.34),
    team(33, "E", "Germany", "GER", "UEFA", "de", 9, 1716.0, 1968, 52745, 84_600_000, 0.94, 0.96),
    team(34, "E", "Curacao", "CUW", "CONCACAF", "cw", 82, 1298.0, 1510, 21400, 150_000, 0.72, 0.02),
    team(35, "E", "Ivory Coast", "CIV", "CAF", "ci", 42, 1487.0, 1705, 2728, 31_000_000, 0.88, 0.24),
    team(36, "E", "Ecuador", "ECU", "CONMEBOL", "ec", 23, 1579.0, 1818, 6630, 18_200_000, 0.9, 0.24),
    team(37, "F", "Netherlands", "NED", "UEFA", "nl", 7, 1745.0, 1987, 61098, 17_900_000, 0.9, 0.78),
    team(38, "F", "Japan", "JPN", "AFC", "jp", 18, 1608.0, 1840, 33834, 124_000_000, 0.74, 0.34),
    team(39, "F", "Sweden", "SWE", "UEFA", "se", 43, 1485.0, 1760, 56305, 10_600_000, 0.8, 0.5),
    team(40, "F", "Tunisia", "TUN", "CAF", "tn", 40, 1493.0, 1698, 3895, 12_400_000, 0.86, 0.16),
    team(41, "G", "Belgium", "BEL", "UEFA", "be", 8, 1731.0, 1940, 53475, 11_800_000, 0.84, 0.66),
    team(42, "G", "Egypt", "EGY", "CAF", "eg", 34, 1516.0, 1726, 3512, 112_000_000, 0.93, 0.22),
    team(43, "G", "Iran", "IRN", "AFC", "ir", 20, 1588.0, 1785, 4502, 89_000_000, 0.84, 0.18),
    team(44, "G", "New Zealand", "NZL", "OFC", "nz", 86, 1275.0, 1490, 48850, 5_300_000, 0.55, 0.06),
    team(45, "H", "Spain", "ESP", "UEFA", "es", 1, 1885.0, 2001, 32677, 48_600_000, 0.94, 0.86),
    team(46, "H", "Cape Verde", "CPV", "CAF", "cv", 68, 1368.0, 1580, 4894, 600_000, 0.82, 0.02),
    team(47, "H", "Saudi Arabia", "KSA", "AFC", "sa", 60, 1400.0, 1648, 32920, 36_900_000, 0.78, 0.18),
    team(48, "H", "Uruguay", "URU", "CONMEBOL", "uy", 16, 1624.0, 1908, 22564, 3_400_000, 0.96, 0.82),
]

PLAYERS = [
    player(1, 1, "Erling Haaland", "ST", 9, 25, "Manchester City", 39, 38, 94),
    player(2, 1, "Martin Odegaard", "CM", 10, 27, "Arsenal", 70, 4, 89),
    player(3, 2, "Kylian Mbappe", "LW", 10, 27, "Real Madrid", 92, 52, 95),
    player(4, 2, "Aurelien Tchouameni", "DM", 8, 26, "Real Madrid", 44, 3, 87),
    player(5, 3, "Sadio Mane", "LW", 10, 34, "Al Nassr", 108, 45, 86),
    player(6, 4, "Aymen Hussein", "ST", 18, 30, "Al Khor", 80, 28, 77),
    player(7, 2, "Bradley Barcola", "LW", 20, 23, "Paris Saint-Germain", 28, 8, 85),
    player(8, 1, "Leo Ostigard", "CB", 4, 26, "Genoa", 31, 2, 78),
    player(9, 5, "Lionel Messi", "AM", 10, 38, "Inter Miami", 200, 112, 94),
    player(10, 7, "Romano Schmid", "AM", 18, 26, "Werder Bremen", 24, 3, 81),
    player(11, 8, "Ali Olwan", "ST", 9, 26, "Al-Faisaly", 77, 19, 76),
    player(12, 7, "Marko Arnautovic", "ST", 7, 37, "Inter", 125, 39, 82),
    player(13, 9, "Joao Neves", "CM", 6, 21, "Paris Saint-Germain", 28, 2, 86),
    player(14, 10, "Yoane Wissa", "ST", 20, 29, "Newcastle United", 34, 7, 82),
    player(15, 13, "Harry Kane", "ST", 9, 32, "Bayern Munich", 112, 74, 92),
    player(16, 13, "Jude Bellingham", "AM", 10, 22, "Real Madrid", 47, 8, 93),
    player(17, 13, "Marcus Rashford", "LW", 11, 28, "Manchester United", 69, 18, 84),
    player(18, 14, "Martin Baturina", "AM", 10, 23, "Dinamo Zagreb", 18, 3, 80),
    player(19, 14, "Petar Musa", "ST", 18, 28, "Benfica", 20, 6, 80),
]

MATCHES = [
    match(1, "I", 2, 3, "2026-06-16T16:00:00+00:00", "New York New Jersey Stadium", "New York/New Jersey", "finished", 3, 1),
    match(2, "I", 4, 1, "2026-06-16T19:00:00+00:00", "Boston Stadium", "Boston", "finished", 1, 4),
    match(3, "I", 1, 3, "2026-06-23T00:00:00+00:00", "New York New Jersey Stadium", "New York/New Jersey"),
    match(4, "I", 2, 4, "2026-06-22T21:00:00+00:00", "Philadelphia Stadium", "Philadelphia"),
    match(5, "I", 1, 2, "2026-06-26T19:00:00+00:00", "Boston Stadium", "Boston"),
    match(6, "I", 3, 4, "2026-06-26T19:00:00+00:00", "Toronto Stadium", "Toronto"),
    match(7, "J", 5, 6, "2026-06-16T22:00:00+00:00", "Kansas City Stadium", "Kansas City", "finished", 3, 0),
    match(8, "J", 7, 8, "2026-06-17T01:00:00+00:00", "San Francisco Bay Area Stadium", "San Francisco Bay Area", "finished", 3, 1),
    match(9, "J", 5, 7, "2026-06-22T17:00:00+00:00", "Dallas Stadium", "Dallas"),
    match(10, "J", 8, 6, "2026-06-23T03:00:00+00:00", "San Francisco Bay Area Stadium", "San Francisco Bay Area"),
    match(11, "J", 6, 7, "2026-06-28T02:00:00+00:00", "Kansas City Stadium", "Kansas City"),
    match(12, "J", 8, 5, "2026-06-28T02:00:00+00:00", "Dallas Stadium", "Dallas"),
    match(13, "K", 9, 10, "2026-06-17T19:00:00+00:00", "Houston Stadium", "Houston", "finished", 1, 1),
    match(14, "K", 9, 11, "2026-06-23T17:00:00+00:00", "Houston Stadium", "Houston"),
    match(15, "K", 12, 10, "2026-06-24T02:00:00+00:00", "Estadio Guadalajara", "Guadalajara"),
    match(16, "K", 12, 9, "2026-06-27T23:30:00+00:00", "Miami Stadium", "Miami"),
    match(17, "K", 10, 11, "2026-06-27T23:30:00+00:00", "Atlanta Stadium", "Atlanta"),
    match(18, "L", 13, 14, "2026-06-17T20:00:00+00:00", "Dallas Stadium", "Dallas", "finished", 4, 2),
    match(19, "L", 13, 15, "2026-06-23T20:00:00+00:00", "Boston Stadium", "Boston"),
    match(20, "L", 16, 14, "2026-06-23T23:00:00+00:00", "Toronto Stadium", "Toronto"),
    match(21, "L", 16, 13, "2026-06-27T21:00:00+00:00", "New York New Jersey Stadium", "New York/New Jersey"),
    match(22, "L", 14, 15, "2026-06-27T21:00:00+00:00", "Philadelphia Stadium", "Philadelphia"),
]

EVENTS = [
    event(1, 1, 2, 3, 66, "Kylian Mbappe sendte Frankrike foran mot Senegal."),
    event(2, 1, 2, 7, 79, "Bradley Barcola doblet ledelsen for Frankrike."),
    event(3, 1, 3, None, 88, "Senegal reduserte sent i kampen."),
    event(4, 1, 2, 3, 90, "Mbappe avgjorde med sitt andre mål.", 4),
    event(5, 2, 1, 1, 18, "Erling Haaland scoret Norges første mål mot Irak."),
    event(6, 2, 4, 6, 39, "Aymen Hussein utlignet for Irak."),
    event(7, 2, 1, 1, 45, "Haaland satte Norge tilbake i ledelsen før pause.", 3),
    event(8, 2, 1, 8, 72, "Leo Ostigard økte ledelsen på dødball."),
    event(9, 2, 1, None, 90, "Norge fikk kampens fjerde scoring på overtid.", 2),
    event(10, 7, 5, 9, 17, "Lionel Messi åpnet scoringen mot Algerie."),
    event(11, 7, 5, 9, 60, "Messi økte Argentinas ledelse."),
    event(12, 7, 5, 9, 76, "Messi fullførte hattricket."),
    event(13, 8, 7, 10, 22, "Romano Schmid sendte Østerrike foran mot Jordan."),
    event(14, 8, 8, 11, 29, "Ali Olwan scoret Jordans første VM-mål."),
    event(15, 8, 7, None, 77, "Østerrike tok ledelsen etter selvmål."),
    event(16, 8, 7, 12, 90, "Marko Arnautovic avgjorde på straffe.", 3),
    event(17, 13, 9, 13, 6, "Joao Neves ga Portugal en tidlig ledelse."),
    event(18, 13, 10, 14, 44, "Yoane Wissa utlignet for DR Congo."),
    event(19, 18, 13, 15, 12, "Harry Kane scoret på straffe mot Kroatia."),
    event(20, 18, 14, 18, 25, "Martin Baturina utlignet for Kroatia."),
    event(21, 18, 13, 15, 40, "Kane headet inn sitt andre mål."),
    event(22, 18, 14, 19, 44, "Petar Musa gjorde 2-2 før pause."),
    event(23, 18, 13, 16, 52, "Jude Bellingham sendte England foran igjen."),
    event(24, 18, 13, 17, 85, "Marcus Rashford punkterte kampen."),
]

LINEUPS = []

LINEUP_PLAYERS = []

BROADCASTS = [
    {
        "id": item_id,
        "match_id": match_id,
        "country_code": "NO",
        "broadcaster": broadcaster,
        "channel": channel,
        "stream_url": stream_url,
        "replay_url": replay_url,
        "requires_login": requires_login,
        "source_url": source_url,
        "last_checked_at": utc("2026-06-18T08:00:00+00:00"),
    }
    for item_id, match_id, broadcaster, channel, stream_url, replay_url, requires_login, source_url in [
        (1, 1, "NRK", "NRK TV", "https://tv.nrk.no/", "https://tv.nrk.no/programmer/sport", False, "https://www.nrk.no/sport/"),
        (2, 2, "TV 2", "TV 2 Play", "https://play.tv2.no/", "https://play.tv2.no/sport", True, "https://www.tv2.no/sport/"),
        (3, 3, "TV 2", "TV 2 Direkte", "https://play.tv2.no/", "https://play.tv2.no/sport", True, "https://www.tv2.no/sport/"),
        (4, 4, "NRK", "NRK", "https://tv.nrk.no/", "https://tv.nrk.no/programmer/sport", False, "https://www.nrk.no/sport/"),
        (5, 5, "TV 2", "TV 2 Sport 1", "https://play.tv2.no/", "https://play.tv2.no/sport", True, "https://www.tv2.no/sport/"),
        (6, 7, "NRK", "NRK TV", "https://tv.nrk.no/", "https://tv.nrk.no/programmer/sport", False, "https://www.nrk.no/sport/"),
        (7, 8, "TV 2", "TV 2 Play", "https://play.tv2.no/", "https://play.tv2.no/sport", True, "https://www.tv2.no/sport/"),
        (8, 13, "TV 2", "TV 2 Play", "https://play.tv2.no/", "https://play.tv2.no/sport", True, "https://www.tv2.no/sport/"),
        (9, 18, "NRK", "NRK TV", "https://tv.nrk.no/", "https://tv.nrk.no/programmer/sport", False, "https://www.nrk.no/sport/"),
    ]
]

LIVE_SNAPSHOTS = []

MODEL_VERSIONS = [
    {
        "version": "wc-v0.1-simple",
        "date": "2026-06-01",
        "notes": "Enkel baseline med FIFA-rangering og Elo.",
    },
    {
        "version": "wc-v0.2-country-features",
        "date": "2026-06-14",
        "notes": "Landmodell med normaliserte landfeatures, økonomiske proxyer og fotballkultur.",
    },
    {
        "version": "wc-v0.3-squad-context",
        "date": "2026-06-23",
        "notes": "Avansert modell med spillerstyrke og kampkontekst fra tilgjengelige data.",
    },
    {
        "version": "wc-v0.4-many-parameters",
        "date": "2026-06-23",
        "notes": "Ekspertmodell med mange parametre, klar for historisk trening og kalibrering.",
    },
]


def seed() -> dict[str, list[dict]]:
    return deepcopy(
        {
            "teams": TEAMS,
            "players": PLAYERS,
            "matches": MATCHES,
            "events": EVENTS,
            "lineups": LINEUPS,
            "lineup_players": LINEUP_PLAYERS,
            "broadcasts": BROADCASTS,
            "live_snapshots": LIVE_SNAPSHOTS,
            "model_versions": MODEL_VERSIONS,
        }
    )


def find_one(collection: str, item_id: int) -> dict | None:
    return next((item for item in seed()[collection] if item["id"] == item_id), None)
