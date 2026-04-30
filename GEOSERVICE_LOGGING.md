# GeoService Debug Logging

## Overview

Debug logging has been added to the GeoService and SignalEnricher to help diagnose issues with country and continent detection.

## Log Files Location

All logs are written to the `/logs/` directory:

- **`logs/geo_service.log`** - Detailed logs for GeoService operations (DEBUG level)
- **`logs/propscope.log`** - General application logs (INFO level)

## Configuration

Logging is configured in `propscope/settings.py`:

- **Console output**: INFO level (simple format)
- **File output**: DEBUG level (verbose format with timestamps, module names, line numbers)
- **Log rotation**: 10MB per file, 5 backup files retained

## What Gets Logged

### GeoService (`apps/geo/services/geo_service.py`)

1. **Initialization**:
   - Geodata loading start
   - Shapefile path and validation
   - Number of records loaded
   - Available columns in shapefile

2. **Country/Continent Lookups**:
   - Each lookup with coordinates
   - Cache hits/misses
   - Coordinate validation warnings
   - Polygon search operations
   - Match results (country and continent)
   - Ocean/unmapped area detection

### SignalEnricher (`apps/ingest/services/enrichment.py`)

1. **Locator Processing**:
   - Locator conversion to coordinates
   - GeoService initialization (lazy load)
   - GeoService detection results
   - MaidenheadArea table lookups
   - Auto-detected vs manual values

## Example Log Output

```
INFO 2026-04-30 07:32:19,345 apps.geo.services.geo_service geo_service _load_geodata:48 Starting GeoService geodata loading process
DEBUG 2026-04-30 07:32:20,222 apps.geo.services.geo_service geo_service _load_geodata:52 geopandas import successful
DEBUG 2026-04-30 07:32:20,222 apps.geo.services.geo_service geo_service _load_geodata:64 Project root: /home/runner/work/PropScope/PropScope
DEBUG 2026-04-30 07:32:20,222 apps.geo.services.geo_service geo_service _load_geodata:65 Shapefile path: /home/runner/work/PropScope/PropScope/geo/ne_110m_admin_0_countries.shp
INFO 2026-04-30 07:32:20,222 apps.geo.services.geo_service geo_service _load_geodata:74 Loading shapefile from: /home/runner/work/PropScope/PropScope/geo/ne_110m_admin_0_countries.shp
INFO 2026-04-30 07:32:20,275 apps.geo.services.geo_service geo_service _load_geodata:77 Shapefile loaded successfully. Records: 177
DEBUG 2026-04-30 07:32:20,275 apps.geo.services.geo_service geo_service get_country_continent:114 get_country_continent called with lat=51.5074, lon=-0.1278
DEBUG 2026-04-30 07:32:20,275 apps.geo.services.geo_service geo_service get_country_continent:123 Cache MISS for (51.5074, -0.1278)
DEBUG 2026-04-30 07:32:20,275 apps.geo.services.geo_service geo_service get_country_continent:148 Searching in 177 polygons
INFO 2026-04-30 07:32:20,278 apps.geo.services.geo_service geo_service get_country_continent:161 Match FOUND for (51.5074, -0.1278): country=United Kingdom, continent=Europe
DEBUG 2026-04-30 07:32:20,279 apps.geo.services.geo_service geo_service get_country_continent:174 Cached result for (51.5074, -0.1278): ('United Kingdom', 'Europe')
```

## Troubleshooting

### No country/continent detected

If you see logs showing `None` results:

```
INFO No match for (0.0, 0.0) - likely ocean or unmapped area
```

This indicates:
- The coordinates are in an ocean or unmapped region
- The shapefile doesn't contain a polygon for that location

### Shapefile not loading

If you see errors during initialization:

```
ERROR Shapefile not found at: /path/to/shapefile
```

Check that:
- The shapefile exists at `/geo/ne_110m_admin_0_countries.shp`
- All required files are present (.shp, .dbf, .shx, .prj, .cpg)

### Cache behavior

Watch for cache hits to verify performance:

```
DEBUG Cache HIT for (51.5074, -0.1278): ('United Kingdom', 'Europe')
```

- First lookup = Cache MISS (lookup performed)
- Subsequent lookups = Cache HIT (instant retrieval)

## Testing

You can test the logging by:

1. Running the management command:
```bash
python manage.py populate_maidenhead_auto --verbosity=2
```

2. Running the backfill command:
```bash
python manage.py backfill_enrichment --verbosity=2
```

3. Importing WSJT-X data with locators

4. Creating/editing MaidenheadArea records in the modal

All GeoService operations will be logged to `logs/geo_service.log`.

## Log File Management

- Logs automatically rotate at 10MB
- Up to 5 backup files are kept
- Older backups are automatically deleted
- Log files are excluded from git (in .gitignore)

## Development Notes

- Console output is at INFO level to avoid cluttering terminal
- File logs are at DEBUG level for detailed diagnostics
- All exceptions include full stack traces in logs (`exc_info=True`)
- Coordinates are logged with full precision for debugging
