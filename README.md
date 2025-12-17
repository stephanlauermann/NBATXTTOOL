# NBA TXT TOOL

Ein simples Python-CLI-Tool zum Abrufen von **NBA-Quoten** und **NBA-Ergebnissen**
und zum Export als **TXT-Dateien**.  

---

## Funktionen

- Abruf von **NBA Moneyline-Quoten (h2h)** für ein bestimmtes Datum
- Abruf von **NBA-Spielergebnissen** für ein bestimmtes Datum
- TXT-Export mit klaren, einheitlichen Zeilenformaten
- Zeitzonen-Umrechnung auf **Europe/Berlin**
- CLI-Menü mit Datums-Eingabe (`TT.MM.JJJJ`)

---

## Voraussetzungen

- Python **3.9 oder höher**
- Python-Paket `requests`
- Internetverbindung

### Installation

```bash
python -m pip install -U requests
```

**Windows-Hinweis:**  
Falls es Probleme mit der Zeitzone gibt, installiere zusätzlich:

```bash
python -m pip install -U tzdata
```

---

## Konfiguration (API-Key)

Für den Abruf der Quoten wird ein API-Key von **The Odds API** benötigt.

Der API-Key wird **nicht im Code gespeichert**, sondern über die
Umgebungsvariable `ODDS_API_KEY` geladen.

### API-Key setzen

#### Windows (PowerShell)

```powershell
setx ODDS_API_KEY "DEIN_API_KEY"
```

Danach ein neues Terminal öffnen.

#### Linux / macOS

```bash
export ODDS_API_KEY="DEIN_API_KEY"
```

> Das Script liest den Key automatisch mit  
> `os.getenv("ODDS_API_KEY")` ein.  
> Fehlt der Key, bricht das Programm mit einer Fehlermeldung ab.

⚠ **Sicherheit:**  
Lege deinen API-Key niemals direkt im Code oder in öffentlichen Repositories ab.

---

## Programmstart

```bash
python nba_txt_tool.py
```

---

## CLI-Menü

```text
1) Quoten für ein Datum holen und als TXT speichern
2) Ergebnisse für ein Datum holen und als TXT speichern
3) Beenden
```

Anschließend wird ein Datum im Format `TT.MM.JJJJ` abgefragt  
(z. B. `14.11.2025`).

---

## Ausgabe-Dateien

### NBA-Quoten

**Dateiname:**

```text
NBA_Quoten_YYYY-MM-DD.txt
```

**Format pro Zeile:**

```text
DD.MM.YYYY HH:MM | Awayteam : Hometeam | QuoteAway | QuoteHome
```

**Beispiel:**

```text
14.11.2025 01:10 | Toronto Raptors : Cleveland Cavaliers | 3,48 | 1,36
```

> Die Quoten sind im **Dezimalformat**  
> mit **Komma** als Dezimaltrenner.

---

### NBA-Ergebnisse

**Dateiname:**

```text
NBA_Ergebnisse_YYYY-MM-DD.txt
```

**Format pro Zeile:**

```text
Awayteam : Hometeam AwayScore:HomeScore
```

**Beispiel:**

```text
Los Angeles Clippers : Los Angeles Lakers 118:135
```

---

## Fehlerbehebung

- **Fehlender API-Key:** Prüfe, ob `ODDS_API_KEY` gesetzt ist
- **Keine Quoten gefunden:** Für das Datum existieren evtl. keine Spiele
- **401 / 403 Fehler:** API-Key ungültig oder Kontingent verbraucht
- **Netzwerkfehler:** Internetverbindung prüfen

---

## Technische Quellen

- Quoten: The Odds API (`basketball_nba`)
- Ergebnisse: Offizielles NBA Scoreboard JSON
- Zeitzone: `Europe/Berlin`

---

README.md für `nba_txt_tool.py`  
API-Key-Verwaltung über Umgebungsvariablen

---

## Author

Created by Stephan Lauermann, AI assisted by ChatGPT.
