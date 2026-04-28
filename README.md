# PropScope
# 📡 PropScope v0.1 (WSJT-X Statistics / CQ Analyzer)

Analyse von WSJT-X `ALL.TXT` Logs mit Fokus auf CQ-Rufe, Entfernung und Ausbreitungsbedingungen.

---

## 🎯 Ziel

Dieses Projekt dient dazu, empfangene CQ-Rufe aus WSJT-X auszuwerten und daraus statistische Erkenntnisse zu gewinnen:

- 📏 Entfernung (Luftlinie) basierend auf Maidenhead Locator
- ⏱️ Auswertung nach Tageszeit
- 📊 Signalqualität (SNR)
- 🌍 Grobe geografische Einordnung (Land/Kontinent)
- 📡 Analyse von Bandöffnungen und Ausbreitungsbedingungen

---

## 🚀 Features (MVP)

- Import von `ALL.TXT`
- Extraktion von CQ-Rufen
- Parsing von:
  - Rufzeichen
  - Locator (4-stellig)
  - SNR
  - Frequenz / Band
  - Zeit
- Berechnung:
  - Locator → Koordinaten
  - Entfernung zum eigenen Standort
- Speicherung in PostgreSQL
- Erste Statistiken:
  - Anzahl CQ je Rufzeichen / Locator
  - Durchschnittlicher SNR
  - Durchschnittliche Entfernung
  - Verteilung nach Uhrzeit

---

## 🧠 Architektur

**Stack:**

- Python
- Django
- HTMX
- Bootstrap 5
- PostgreSQL

**Konzept:**

WSJT-X ALL.TXT → Parser → Enrichment → DB → Statistik/UI

---

## 📍 Maidenhead Locator

WSJT-X liefert in der Regel **4-stellige Maidenhead Locator** (z. B. `JN68`).

Diese werden verwendet für:

- Berechnung eines Mittelpunktes (Lat/Lon)
- Abschätzung der Entfernung (Luftlinie)

⚠️ Einschränkungen:

- Genauigkeit: ~100–150 km
- Keine exakte Positionsbestimmung
- Grenzgebiete können mehrere Länder enthalten

---

## 📡 Rufzeichen

Rufzeichen werden analysiert für:

- Land (Prefix-Auswertung)
- optional Klasse (z. B. Deutschland gemäß BNetzA)

QRZ-Link:

https://www.qrz.com/db/<CALLSIGN>

---

## 🗄️ Datenmodell (vereinfacht)

```python
class HeardCQ(models.Model):
    timestamp = models.DateTimeField()
    band_mhz = models.FloatField()
    snr = models.IntegerField()

    callsign = models.CharField(max_length=32)
    callsign_country = models.CharField(max_length=100, null=True)

    locator = models.CharField(max_length=4, null=True)
    locator_lat = models.FloatField(null=True)
    locator_lon = models.FloatField(null=True)

    distance_km = models.FloatField(null=True)

    locator_country = models.CharField(max_length=100, null=True)
    locator_ambiguous = models.BooleanField(default=False)
```

---

## 📊 Beispiel-Analysen

- Entfernung vs. Tageszeit
- Bandöffnung
- SNR vs. Entfernung
- Verteilung nach Locator
- Entwicklung über Zeit

---

## 🛠️ Setup

### Voraussetzungen

- Python 3.12+
- PostgreSQL 12+
- Git

### Installation

1. **Repository klonen:**

```bash
git clone <repository-url>
cd PropScope
```

2. **Virtual Environment erstellen:**

```bash
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate
```

3. **Dependencies installieren:**

```bash
pip install -r requirements.txt
```

4. **Umgebungsvariablen konfigurieren:**

```bash
cp .env.example .env
```

Bearbeiten Sie die `.env` Datei und passen Sie die Werte an:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (PostgreSQL)
DB_NAME=propscope
DB_USER=propscope
DB_PASSWORD=your-password-here
DB_HOST=localhost
DB_PORT=5432
```

5. **PostgreSQL Datenbank erstellen:**

```bash
createdb propscope
createuser propscope
# Passwort für User setzen
psql -c "ALTER USER propscope WITH PASSWORD 'your-password-here';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE propscope TO propscope;"
```

6. **Datenbank migrieren:**

```bash
python manage.py migrate
```

7. **Server starten:**

```bash
python manage.py runserver
```

Die Anwendung ist nun unter http://localhost:8000 erreichbar.

### Admin-User erstellen

```bash
python manage.py createsuperuser
```

---

## 📥 Import

```bash
python manage.py import_all_txt /path/to/ALL.TXT
```

---

## 🔮 Roadmap

### Phase 1
- CQ Parser
- Locator → Entfernung
- Basisstatistiken

### Phase 2
- Locator → Länder-Mapping
- Rufzeichen-Datenbank
- UI Filter

### Phase 3
- Reverse Geocoding
- Karten
- Heatmaps
- Echtzeit-Import

---

## ⚠️ Disclaimer

- Locator-Daten sind Näherungen
- Länderzuordnung kann ungenau sein

