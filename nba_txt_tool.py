import requests
import datetime as dt
from zoneinfo import ZoneInfo  # Python 3.9+, unter Windows ggf. `pip install tzdata`
from typing import List, Dict

# ============================================================
# KONFIGURATION
# ============================================================

# !!! HIER DEIN API-KEY VON "The Odds API" EINTRAGEN !!!
API_KEY = "DEINAPIKEY"

ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
NBA_SCOREBOARD_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"

TIMEZONE = "Europe/Berlin"
LOCAL_TZ = ZoneInfo(TIMEZONE)


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def parse_date_input(date_str: str) -> dt.date:
    """
    Erwartet Datum im Format TT.MM.JJJJ und gibt datetime.date zurück.
    """
    return dt.datetime.strptime(date_str.strip(), "%d.%m.%Y").date()


def to_local_datetime(iso_str: str) -> dt.datetime:
    """
    ISO-String (UTC) -> lokale Zeit (Europe/Berlin).
    Beispiel: "2025-11-25T18:00:00Z"
    """
    # "Z" durch Offset ersetzen
    if iso_str.endswith("Z"):
        iso_str = iso_str.replace("Z", "+00:00")
    dt_utc = dt.datetime.fromisoformat(iso_str)
    return dt_utc.astimezone(LOCAL_TZ)


def fcomma(value: float) -> str:
    """
    Float -> String mit 2 Nachkommastellen und Komma als Dezimaltrenner.
    1.25 -> "1,25"
    """
    return f"{value:.2f}".replace(".", ",")


# ============================================================
# QUOTEN HOLEN (The Odds API)
# ============================================================

def fetch_odds(api_key: str, target_date: dt.date) -> List[Dict]:
    """
    Holt Quoten (moneyline / h2h) für NBA-Spiele an target_date.

    Rückgabe: Liste von Dicts mit:
      - datetime_str (lokal)
      - away_team
      - home_team
      - odds_away
      - odds_home
    """
    params = {
        "apiKey": api_key,
        "regions": "eu",       # europäische Bookies
        "markets": "h2h",      # moneyline
        "dateFormat": "iso",
        "oddsFormat": "decimal",
    }

    print("Hole Quoten von The Odds API...")
    resp = requests.get(ODDS_API_URL, params=params, timeout=20)
    resp.raise_for_status()
    events = resp.json()

    games_out = []

    for ev in events:
        try:
            commence_local = to_local_datetime(ev["commence_time"])
        except Exception:
            continue

        if commence_local.date() != target_date:
            continue

        home = ev.get("home_team")
        away = ev.get("away_team")
        if not home or not away:
            continue

        odds_home = None
        odds_away = None

        for bm in ev.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                for out in market.get("outcomes", []):
                    name = out.get("name")
                    price = out.get("price")
                    if name == away:
                        odds_away = float(price)
                    elif name == home:
                        odds_home = float(price)
                if odds_home is not None and odds_away is not None:
                    break
            if odds_home is not None and odds_away is not None:
                break

        if odds_home is None or odds_away is None:
            # Wenn bei diesem Event keine kompletten Quoten gefunden werden, überspringen
            continue

        games_out.append(
            {
                "datetime_str": commence_local.strftime("%d.%m.%Y %H:%M"),
                "away_team": away,
                "home_team": home,
                "odds_away": odds_away,
                "odds_home": odds_home,
            }
        )

    return games_out


def format_odds_line(game: Dict) -> str:
    """
    Format:
      "Datum Uhrzeit | Awayteam : Hometeam | Quote Away | Quote Home"
    Beispiel:
      "14.11.2025 01:10 | Toronto Raptors : Cleveland Cavaliers | 3,48 | 1,36"
    """
    return (
        f"{game['datetime_str']} | "
        f"{game['away_team']} : {game['home_team']} | "
        f"{fcomma(game['odds_away'])} | {fcomma(game['odds_home'])}"
    )


def write_odds_file(games: List[Dict], target_date: dt.date) -> str:
    """
    Schreibt die Quoten in eine Textdatei.
    Dateiname: NBA_Quoten_YYYY-MM-DD.txt
    """
    filename = f"NBA_Quoten_{target_date.isoformat()}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for g in games:
            line = format_odds_line(g)
            f.write(line + "\n")

    return filename


# ============================================================
# ERGEBNISSE HOLEN (NBA Scoreboard JSON)
# ============================================================

def fetch_results(target_date: dt.date) -> List[Dict]:
    """
    Holt Ergebnisse vom offiziellen NBA-Scoreboard-JSON.

    Rückgabe: Liste von Dicts mit:
      - datetime_str (lokal)  -> intern noch vorhanden, aber NICHT in Datei geschrieben
      - away_team
      - home_team
      - score_away
      - score_home
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (NBA-Results-Script)",
        "Referer": "https://www.nba.com/",
        "Accept": "application/json",
    }

    print("Hole Ergebnisse vom NBA Scoreboard...")
    resp = requests.get(NBA_SCOREBOARD_URL, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    games = data.get("scoreboard", {}).get("games", [])
    games_out = []

    for g in games:
        try:
            local_dt = to_local_datetime(g["gameTimeUTC"])
        except Exception:
            continue

        # Nur Spiele des gewünschten Tages (lokale Zeit) berücksichtigen
        if local_dt.date() != target_date:
            continue

        home = g.get("homeTeam", {})
        away = g.get("awayTeam", {})

        # Vollständiger Teamname: "Los Angeles Lakers" etc.
        home_name = f"{home.get('teamCity', '').strip()} {home.get('teamName', '').strip()}".strip()
        away_name = f"{away.get('teamCity', '').strip()} {away.get('teamName', '').strip()}".strip()

        try:
            home_score = int(home.get("score", 0))
            away_score = int(away.get("score", 0))
        except (TypeError, ValueError):
            home_score = away_score = 0

        games_out.append(
            {
                "datetime_str": local_dt.strftime("%d.%m.%Y %H:%M"),
                "away_team": away_name,
                "home_team": home_name,
                "score_away": away_score,
                "score_home": home_score,
            }
        )

    return games_out


def format_result_line(game: Dict) -> str:
    """
    NEUES Format für Ergebnisse OHNE Datum/Uhrzeit:

      "Awayteam : Hometeam AwayScore:HomeScore"

    Beispiel:
      "Los Angeles Clippers : Los Angeles Lakers 118:135"
    """
    return (
        f"{game['away_team']} : {game['home_team']} "
        f"{game['score_away']}:{game['score_home']}"
    )


def write_results_file(games: List[Dict], target_date: dt.date) -> str:
    """
    Schreibt die Ergebnisse in eine Textdatei.
    Dateiname: NBA_Ergebnisse_YYYY-MM-DD.txt

    Jede Zeile im Format (ohne Datum/Uhrzeit):
      Awayteam : Hometeam AwayScore:HomeScore
    """
    filename = f"NBA_Ergebnisse_{target_date.isoformat()}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for g in games:
            line = format_result_line(g)
            f.write(line + "\n")

    return filename


# ============================================================
# HAUPTMENÜ / CLI
# ============================================================

def menu():
    print("========================================")
    print(" NBA TXT TOOL")
    print("========================================")
    print("1) Quoten für ein Datum holen und als TXT speichern")
    print("2) Ergebnisse für ein Datum holen und als TXT speichern")
    print("3) Beenden")
    print("========================================")

    choice = input("Auswahl (1/2/3): ").strip()
    return choice


def main():
    while True:
        choice = menu()

        if choice == "3":
            print("Beende Programm.")
            break

        if choice not in ("1", "2"):
            print("Ungültige Auswahl.")
            continue

        date_str = input("Bitte Datum eingeben (TT.MM.JJJJ): ").strip()
        try:
            target_date = parse_date_input(date_str)
        except ValueError:
            print("Ungültiges Datum. Bitte Format TT.MM.JJJJ verwenden.")
            continue

        if choice == "1":
            # QUOTEN
            if not API_KEY or API_KEY == "DEIN_API_KEY_HIER":
                print("FEHLER: Kein gültiger API_KEY eingetragen. Bitte im Skript API_KEY setzen.")
                continue

            try:
                games = fetch_odds(API_KEY, target_date)
            except Exception as e:
                print(f"Fehler beim Holen der Quoten: {e}")
                continue

            if not games:
                print("Keine Quoten für dieses Datum gefunden.")
                continue

            filename = write_odds_file(games, target_date)
            print(f"{len(games)} Quoten gespeichert in: {filename}")

        elif choice == "2":
            # ERGEBNISSE
            try:
                games = fetch_results(target_date)
            except Exception as e:
                print(f"Fehler beim Holen der Ergebnisse: {e}")
                continue

            if not games:
                print("Keine Ergebnisse für dieses Datum gefunden.")
                continue

            filename = write_results_file(games, target_date)
            print(f"{len(games)} Ergebnisse gespeichert in: {filename}")
            print("Format der Zeilen: Awayteam : Hometeam AwayScore:HomeScore")

        input("\nWeiter mit Enter...")


if __name__ == "__main__":
    main()
