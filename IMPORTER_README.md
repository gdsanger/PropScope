# WSJT-X ALL.TXT Importer

This document describes the WSJT-X ALL.TXT importer for PropScope.

## Overview

The importer processes WSJT-X `ALL.TXT` log files, extracts CQ calls, enriches them with computed data, and stores them in the database for analysis.

## Features

- **CQ Detection**: Only imports CQ calls from the log file
- **Deduplication**: Uses SHA256 hash to prevent duplicate imports
- **Enrichment**: Automatically computes:
  - Band from frequency
  - QRZ.com URLs
  - Locator coordinates (lat/lon)
  - Distance from home station
  - Country/continent from callsign prefix (if in database)
  - Country/continent from locator (if in database)
- **Incremental Import**: Tracks file position to only import new lines
- **Robust Error Handling**: Skips invalid lines without failing the entire import

## Usage

### Manual Import

Import an entire file:

```bash
python manage.py import_all_txt /path/to/ALL.TXT --full
```

Import only new lines (incremental):

```bash
python manage.py import_all_txt /path/to/ALL.TXT --incremental
```

Default is incremental mode:

```bash
python manage.py import_all_txt /path/to/ALL.TXT
```

### Periodic Polling (Cron)

The `poll_wsjtx_log` command is designed for periodic execution via cron:

```bash
python manage.py poll_wsjtx_log
```

This command:
- Reads the file path from PropScopeSettings or environment variable
- Imports only new lines since last position
- Updates the last position in PropScopeSettings
- Exits gracefully if file doesn't exist yet

#### Cron Configuration

To run every minute:

```cron
*/1 * * * * /path/to/venv/bin/python /path/to/propscope/manage.py poll_wsjtx_log >> /var/log/propscope/import.log 2>&1
```

For quieter output:

```cron
*/1 * * * * /path/to/venv/bin/python /path/to/propscope/manage.py poll_wsjtx_log --quiet >> /var/log/propscope/import.log 2>&1
```

## Configuration

### PropScopeSettings

Configure the importer via the Django admin or database:

- `wsjtx_all_txt_path`: Path to the WSJT-X ALL.TXT file
- `wsjtx_poll_interval_seconds`: Recommended polling interval (default: 30)
- `wsjtx_last_position`: Automatically updated with last read position
- `station_locator`: Your home station Maidenhead locator (for distance calculation)
- `station_latitude`: Your home station latitude
- `station_longitude`: Your home station longitude

### Environment Variables

You can also configure via environment variables in `.env`:

```env
WSJTX_ALL_TXT_PATH=/path/to/ALL.TXT
WSJTX_POLL_INTERVAL=30
```

## WSJT-X ALL.TXT Format

Example line:

```
260419_185200     7.074 Rx FT8    -19  0.3 1133 CQ EX7CQ MN72
```

Fields:
- `260419_185200`: Timestamp (DDMMYY_HHMMSS)
- `7.074`: Frequency in MHz
- `Rx`: Direction (Rx = received, Tx = transmitted)
- `FT8`: Mode
- `-19`: SNR (Signal-to-Noise Ratio) in dB
- `0.3`: DT (time offset) in seconds
- `1133`: Audio frequency in Hz
- `CQ EX7CQ MN72`: Decoded message

## Import Process

1. **Parse**: Each line is parsed and validated
2. **Filter**: Only CQ calls are processed
3. **Hash**: Calculate SHA256 hash of raw line for deduplication
4. **Check Duplicates**: Skip if hash already exists
5. **Enrich**: Add computed fields:
   - Band from frequency
   - QRZ URL from callsign
   - Lat/lon from locator
   - Distance from home station
   - Country/continent lookups
6. **Save**: Store HeardSignal in database
7. **Track**: Update import statistics and file position

## Models

### ImportRun

Tracks each import execution:

- `source_filename`: Path to imported file
- `started_at`: Import start time
- `finished_at`: Import completion time
- `lines_total`: Total lines processed
- `lines_imported`: Successfully imported CQ calls
- `lines_skipped`: Skipped lines (non-CQ, duplicates, errors)
- `status`: pending, running, completed, failed
- `notes`: Error messages or additional information

### HeardSignal

Stores each CQ call:

**Signal Data:**
- `timestamp`: When received
- `frequency_mhz`: Frequency
- `band`: Band (e.g., "20m", "40m")
- `mode`: Mode (e.g., "FT8", "FT4")
- `snr`: Signal-to-noise ratio in dB
- `dt`: Time offset in seconds
- `audio_frequency`: Audio frequency in Hz
- `raw_message`: Original decoded message
- `raw_line`: Complete raw line from file
- `raw_hash`: SHA256 hash for deduplication

**Callsign Information:**
- `callsign`: Callsign
- `callsign_country`: Country from prefix lookup
- `callsign_continent`: Continent from prefix lookup
- `qrz_url`: QRZ.com lookup URL

**Locator Information:**
- `locator`: Maidenhead locator
- `locator_lat`: Latitude from locator
- `locator_lon`: Longitude from locator
- `locator_country`: Country from locator lookup
- `locator_alt_country`: Alternative country (border areas)
- `locator_continent`: Continent from locator lookup
- `locator_ambiguous`: True if spans multiple countries

**Distance:**
- `distance_km`: Distance from home station in km

**Metadata:**
- `import_run`: Reference to ImportRun
- `created_at`: Record creation time
- `updated_at`: Record update time

## Architecture

```
┌──────────────────┐
│  WSJT-X ALL.TXT  │
└────────┬─────────┘
         │
         v
┌────────────────────────┐
│  WsjtxLineParser       │
│  - Parse line          │
│  - Extract timestamp   │
│  - Detect CQ           │
│  - Extract callsign    │
│  - Extract locator     │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│  SignalEnricher        │
│  - Calculate band      │
│  - Generate QRZ URL    │
│  - Convert locator     │
│  - Calculate distance  │
│  - Lookup country      │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│  WsjtxLogImporter      │
│  - Manage import run   │
│  - Check duplicates    │
│  - Track position      │
│  - Handle errors       │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│  Database              │
│  - ImportRun           │
│  - HeardSignal         │
└────────────────────────┘
```

## Utilities

### Geo Utils (`apps/geo/utils.py`)

- `maidenhead_to_latlon(locator)`: Convert locator to coordinates
- `haversine_distance(lat1, lon1, lat2, lon2)`: Calculate distance
- `calculate_distance_from_locators(loc1, loc2)`: Distance between locators
- `frequency_to_band(frequency_mhz)`: Determine amateur radio band

### Callsign Utils (`apps/callsign/utils.py`)

- `normalize_callsign(callsign)`: Remove suffixes (/P, /M, etc.)
- `extract_prefix(callsign)`: Get country prefix
- `generate_qrz_url(callsign)`: Generate QRZ.com URL

## Testing

Run tests:

```bash
python manage.py test apps.ingest
```

The test suite covers:
- WSJT-X line parsing (valid/invalid formats)
- CQ detection
- Maidenhead locator conversion
- Distance calculation
- Frequency to band conversion
- Callsign utilities

## Example Workflow

1. Configure your home station in PropScopeSettings:
   ```python
   from apps.ui.models import PropScopeSettings
   settings = PropScopeSettings.objects.get_or_create(name='default')[0]
   settings.station_locator = 'JN68qv'
   settings.station_latitude = 48.5
   settings.station_longitude = 8.0
   settings.wsjtx_all_txt_path = '/home/user/.local/share/WSJT-X/ALL.TXT'
   settings.save()
   ```

2. Run initial import:
   ```bash
   python manage.py import_all_txt /home/user/.local/share/WSJT-X/ALL.TXT --full
   ```

3. Set up cron for periodic updates:
   ```cron
   */1 * * * * /path/to/venv/bin/python /path/to/propscope/manage.py poll_wsjtx_log --quiet
   ```

4. View imported signals in Django admin or via API

## Troubleshooting

### No signals imported

- Check that the file contains CQ calls (not just QSOs)
- Verify file format matches WSJT-X ALL.TXT format
- Check import run notes for errors

### Duplicates not working

- Ensure migrations are up to date: `python manage.py migrate`
- Check that `raw_hash` field exists in HeardSignal model

### Distance not calculated

- Verify `station_latitude` and `station_longitude` are set in PropScopeSettings
- Ensure locator is valid 4 or 6 character format

### File not found in poll command

- Set `wsjtx_all_txt_path` in PropScopeSettings
- Or set `WSJTX_ALL_TXT_PATH` environment variable
- Or use `--file` option

## Limitations

- Only processes CQ calls (other messages are skipped)
- Maidenhead locators provide approximate location (100-150km accuracy)
- Country/continent lookup requires data in CallsignPrefix and MaidenheadArea tables
- File must be readable and in WSJT-X ALL.TXT format

## Future Enhancements

Not included in this implementation (see other issues):
- Real-time monitoring via file watching
- WebSocket updates to UI
- Email notifications via Graph API
- Advanced statistics and visualizations
- Automatic country/continent database population
