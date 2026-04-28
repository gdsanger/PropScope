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

```bash
git clone <repo>
cd wsjtx-stats

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
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

