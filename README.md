# CryptoTrader - Bitvavo Automated Trading

Automatisierter Krypto-Handel ueber die Bitvavo API mit Terminal-UI (Textual), Backtesting, Risikomanagement und Telegram-Benachrichtigungen.

## Features

- **Live & Paper Trading** ueber die Bitvavo API
- **4 Strategien**: Moving Average Crossover, RSI, Bollinger Bands, Composite
- **Backtesting** mit Parameter-Sweep und Heatmap-Visualisierung
- **Risikomanagement**: Position Sizing, Stop Loss, Take Profit, Max Drawdown
- **Terminal-UI** mit 4 Screens: Dashboard, Backtest, Orders, Logs
- **Telegram-Benachrichtigungen** bei Trades (optional)
- **SQLite-Persistenz** fuer Trade-History

## Voraussetzungen

- Python 3.11 oder hoeher
- Ein Bitvavo-Konto (nur fuer Live-Trading, nicht fuer Paper/Backtest)

## Installation

```bash
git clone <repository-url>
cd bitvavo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Konfiguration

Es gibt zwei Konfigurationsdateien: `.env` fuer geheime Zugangsdaten und `config.yaml` fuer alle Handelseinstellungen.

### Schnellstart (Paper Trading / Backtesting)

Fuer Paper Trading und Backtesting werden keine API-Keys benoetigt. Es genuegt eine `config.yaml`:

```bash
cp config.example.yaml config.yaml
```

Fertig — die App laeuft sofort im Paper-Modus mit Standardwerten.

### Vollstaendige Einrichtung (Live Trading + Telegram)

#### 1. `.env` — Geheime Zugangsdaten

```bash
cp .env.example .env
```

Folgende Werte in `.env` eintragen:

| Variable | Woher | Wofuer |
|---|---|---|
| `BITVAVO_API_KEY` | Bitvavo → Einstellungen → API | Pflicht fuer Live-Trading |
| `BITVAVO_API_SECRET` | Wird zusammen mit dem Key generiert | Pflicht fuer Live-Trading |
| `TELEGRAM_BOT_TOKEN` | Telegram BotFather (siehe unten) | Optional — Trade-Benachrichtigungen |
| `TELEGRAM_CHAT_ID` | Telegram userinfobot (siehe unten) | Optional — Empfaenger der Nachrichten |

**Bitvavo API Key erstellen:**

1. Auf https://account.bitvavo.com einloggen
2. Einstellungen → API → "Neuen API-Key erstellen"
3. Berechtigungen: **Lesen** und **Handeln** aktivieren, **Auszahlung deaktiviert** lassen
4. Key und Secret kopieren und in `.env` eintragen

**Telegram Bot einrichten (optional):**

1. In Telegram `@BotFather` anschreiben → `/newbot` → Bot-Token kopieren
2. `@userinfobot` anschreiben → eigene Chat-ID kopieren
3. Beides in `.env` eintragen

#### 2. `config.yaml` — Handelseinstellungen

```bash
cp config.example.yaml config.yaml
```

Die Datei ist in Abschnitte gegliedert:

**`trading` — Grundeinstellungen:**

| Einstellung | Werte | Beschreibung |
|---|---|---|
| `mode` | `"paper"` / `"live"` | Paper = Simulation ohne echtes Geld. Immer zuerst mit paper testen! |
| `market` | z.B. `"BTC-EUR"`, `"ETH-EUR"` | Handelspaar auf Bitvavo |
| `interval` | `"1m"`, `"5m"`, `"15m"`, `"30m"`, `"1h"`, `"2h"`, `"4h"`, `"6h"`, `"8h"`, `"12h"`, `"1d"` | Wie oft der Bot eine Handelsentscheidung trifft |
| `max_open_orders` | Zahl, z.B. `3` | Maximale gleichzeitige offene Orders |

**`strategy` — Strategiewahl:**

| Einstellung | Werte | Beschreibung |
|---|---|---|
| `name` | `"ma_crossover"`, `"rsi"`, `"bollinger"`, `"composite"` | Aktive Strategie |

Die Parameter jeder Strategie koennen darunter angepasst werden (siehe Abschnitt Strategien).

**`risk` — Risikomanagement:**

| Einstellung | Default | Beschreibung |
|---|---|---|
| `max_position_pct` | `0.25` | Max. 25% des Portfolios in eine Position |
| `max_drawdown_pct` | `0.10` | Trading stoppt bei 10% Verlust vom Hoechststand |
| `stop_loss_pct` | `0.05` | Automatischer Verkauf bei 5% Verlust |
| `take_profit_pct` | `0.10` | Automatischer Verkauf bei 10% Gewinn |
| `max_daily_trades` | `10` | Maximal 10 Trades pro Tag |

**`backtest` — Backtesting:**

| Einstellung | Default | Beschreibung |
|---|---|---|
| `initial_capital` | `10000.0` | Startkapital in EUR (auch fuer Paper Trading) |
| `fee_pct` | `0.0025` | Simulierte Handelsgebuehr (0.25%) |

**`telegram` — Benachrichtigungen:**

| Einstellung | Default | Beschreibung |
|---|---|---|
| `enabled` | `false` | Auf `true` setzen, um Benachrichtigungen zu aktivieren |

**`database` — Datenbank:**

| Einstellung | Default | Beschreibung |
|---|---|---|
| `path` | `"trades.db"` | Pfad zur SQLite-Datenbankdatei |

### Was wird wofuer benoetigt?

| Anwendungsfall | `.env` noetig? | `config.yaml` noetig? |
|---|---|---|
| Backtesting | Nein | Ja (oder Defaults) |
| Paper Trading | Nein | Ja (oder Defaults) |
| Live Trading | Ja (API Key + Secret) | Ja mit `mode: "live"` |
| Mit Telegram | Ja (Bot Token + Chat ID) | Ja mit `telegram.enabled: true` |

## Verwendung

```bash
# Virtuelle Umgebung aktivieren
source .venv/bin/activate

# Standard (Paper Trading, Default Config)
PYTHONPATH=src python -m cryptotrader

# Mit eigener Config-Datei
PYTHONPATH=src python -m cryptotrader -c config.yaml

# Verbose Logging (Debug-Informationen in cryptotrader.log)
PYTHONPATH=src python -m cryptotrader -v
```

Alternativ aus dem `src/`-Verzeichnis:

```bash
cd src
python -m cryptotrader
```

Log-Ausgaben werden in die Datei `cryptotrader.log` geschrieben.

## TUI-Navigation

| Taste | Aktion |
|-------|--------|
| `1` | Dashboard-Screen |
| `2` | Backtest-Screen |
| `3` | Orders-Screen |
| `4` | Log-Screen |
| `Space` | Trading starten / stoppen (Dashboard) |
| `r` | Orders aktualisieren (Orders-Screen) |
| `c` | Logs loeschen (Log-Screen) |
| `q` | Programm beenden |

## Screens

### Dashboard (Taste 1)
- Aktueller Preis mit Sparkline-Chart
- Portfolio-Uebersicht: Cash, Positionen, unrealisierter PnL
- Strategie-Status: aktive Strategie und letztes Signal (BUY/SELL/HOLD)
- Mit `Space` wird der automatische Trading-Loop gestartet oder gestoppt

### Backtest (Taste 2)
- Strategie per Dropdown auswaehlen
- "Run Sweep" startet einen Parameter-Sweep ueber alle Parameterkombinationen
- Ergebnisse als Heatmap (Sharpe Ratio) und sortierte Tabelle
- Zeigt: Return %, Sharpe Ratio, Max Drawdown, Win Rate, Anzahl Trades

### Orders (Taste 3)
- Trade-History aus der SQLite-Datenbank
- Spalten: Zeitstempel, Markt, Seite (BUY/SELL), Menge, Preis, Gebuehren, PnL, Strategie
- Mit `r` aktualisieren

### Logs (Taste 4)
- Scrollbarer Log-View mit allen Trading-Events
- Signale, ausgefuehrte Trades, Risk-Entscheidungen, Fehler
- Mit `c` loeschen

## Strategien

### Moving Average Crossover (`ma_crossover`)

Vergleicht einen schnellen mit einem langsamen gleitenden Durchschnitt.

- **Kaufsignal**: Schneller MA kreuzt den langsamen MA von unten nach oben
- **Verkaufssignal**: Schneller MA kreuzt den langsamen MA von oben nach unten
- Parameter: `fast_period` (Default: 10), `slow_period` (Default: 30)

### RSI (`rsi`)

Relative Strength Index — misst ob ein Asset ueberkauft oder ueberverkauft ist.

- **Kaufsignal**: RSI faellt unter die Oversold-Schwelle (Default: 30)
- **Verkaufssignal**: RSI steigt ueber die Overbought-Schwelle (Default: 70)
- Parameter: `period` (Default: 14), `overbought` (Default: 70), `oversold` (Default: 30)

### Bollinger Bands (`bollinger`)

Berechnet ein Band um den gleitenden Durchschnitt basierend auf der Standardabweichung.

- **Kaufsignal**: Preis beruehrt oder unterschreitet das untere Band
- **Verkaufssignal**: Preis beruehrt oder ueberschreitet das obere Band
- Parameter: `period` (Default: 20), `std_dev` (Default: 2.0)

### Composite (`composite`)

Kombiniert mehrere Strategien und entscheidet per Abstimmung.

- **`unanimous`**: Alle Strategien muessen dasselbe Signal geben
- **`majority`**: Mehr als die Haelfte muss uebereinstimmen
- **`any`**: Ein einziges Signal genuegt
- Parameter: `strategies` (Liste der Strategienamen), `mode` (Abstimmungsmodus)

## Risikomanagement

Der RiskManager prueft jede Order vor der Ausfuehrung:

- **Max Position Size**: Begrenzt den Anteil des Portfolios, der in eine einzelne Position fliessen darf. Wird die Grenze ueberschritten, wird die Ordergroesse automatisch reduziert.
- **Stop Loss**: Automatischer Verkauf, wenn der Preis um den konfigurierten Prozentsatz unter den Einstiegspreis faellt.
- **Take Profit**: Automatischer Verkauf, wenn der Preis um den konfigurierten Prozentsatz ueber den Einstiegspreis steigt.
- **Max Drawdown**: Trading wird gestoppt, wenn das Portfolio um den konfigurierten Prozentsatz vom Hoechststand gefallen ist.
- **Max Daily Trades**: Maximale Anzahl Trades pro Tag, um Overtrading zu verhindern.

## Architektur

```
config.yaml / .env
        |
        v
  Config Loader --> AppConfig
                        |
                        v
  Bitvavo API --> TradingClient (Live/Paper) --> Candles
                                                    |
                                                    v
                                          Strategy.evaluate() --> Signal
                                                    |
                                                    v
                                          RiskManager.check_order()
                                                    |
                                            erlaubt / blockiert
                                                    |
                                                    v
                                          TradingClient.place_order() --> Order
                                                    |
                                                    v
                                    TradeRepository.insert() + TelegramNotifier
                                                    |
                                                    v
                                              TUI Update
```

### Design-Entscheidungen

- **TradingClient als Protocol**: Strukturelles Subtyping — Live-Client und Paper-Client implementieren dasselbe Interface ohne gemeinsame Basisklasse. Erleichtert Testing und Erweiterbarkeit.
- **Synchrone Strategien, asynchrone Engine**: `evaluate()` ist CPU-bound und braucht kein I/O. Die Engine und der Trading-Loop laufen asynchron.
- **`asyncio.to_thread()`** fuer die Bitvavo SDK: Die offizielle SDK ist synchron, `to_thread` vermeidet Blocking des Event Loops.
- **`ProcessPoolExecutor`** fuer Backtesting: Parameter-Sweeps sind CPU-bound und embarrassingly parallel. Mehrere Kombinationen werden gleichzeitig in separaten Prozessen berechnet.
- **Null Object Pattern** fuer Telegram: `NullNotifier` statt `if enabled`-Checks im gesamten Code.
- **aiosqlite**: Nicht-blockierendes SQLite im async Event Loop.
- **Pydantic fuer Config, Dataclasses fuer Domain Models**: Validierung wo noetig (Konfiguration), Performance wo wichtig (Candles, Orders im Hot Path).

### Projektstruktur

```
src/cryptotrader/
  config/         Pydantic-Konfigurationsmodelle, YAML/.env-Loader
  models/         Datenklassen: Candle, Order, Signal, Trade, Portfolio
  api/            TradingClient Protocol, Bitvavo-Client, Paper-Client
  strategies/     Strategy ABC, MA Crossover, RSI, Bollinger, Composite
  engine/         TradingEngine Orchestrator, async Trading Loop
  backtesting/    BacktestEngine, ParameterSweep, Metriken
  risk/           RiskManager
  db/             SQLite-Verbindung, TradeRepository
  notifications/  Telegram-Notifier, NullNotifier
  tui/
    screens/      Dashboard, Backtest, Orders, Logs
    widgets/      Heatmap, PriceChart, PortfolioSummary, StrategyPanel
    styles/       TCSS-Styling
  app.py          Hauptanwendung mit Screen-Navigation
  __main__.py     Entry Point
```

## Sicherheitshinweise

- **Niemals** `.env` in Git committen — die Datei ist in `.gitignore` eingetragen.
- Bitvavo API Key **ohne Auszahlungsrecht** erstellen.
- Zuerst **immer im Paper-Modus testen**, bevor Live-Trading aktiviert wird.
- `config.yaml` enthaelt keine Geheimnisse und kann committet werden, `.env` nicht.
- Der Bot handelt automatisch — Risikomanagement-Einstellungen vor dem Start sorgfaeltig pruefen.

## Lizenz

Siehe [LICENSE](LICENSE).
