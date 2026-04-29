# Core Services: Callsign + Band Detection

This document describes the core services for callsign analysis and band detection in PropScope.

## Overview

PropScope uses two core services for signal enrichment:

1. **CallsignService** - Analyzes callsigns and detects country/continent from prefix
2. **BandService** - Detects amateur radio band from frequency

All prefix and band data is stored in database tables, with **no hardcoded data in the code**.

## Services

### CallsignService

Located in: `apps/callsign/services/callsign_service.py`

#### Features

- Normalize callsigns (trim, uppercase, remove brackets)
- Generate QRZ.com lookup URLs
- Detect country/continent from callsign prefix (database-driven)
- Handle portable callsigns (e.g., `DL/AD2LX`, `EA8/DL1ABC`)
- Longest-match algorithm for prefix detection
- Detect German license classes (optional, database-driven)

#### Usage Example

```python
from apps.callsign.services import CallsignService

service = CallsignService()

# Normalize callsign
callsign = service.normalize_callsign(" dl3tx ")
# Returns: "DL3TX"

# Generate QRZ URL
url = service.get_qrz_url("DL3TX")
# Returns: "https://www.qrz.com/db/DL3TX"

# Detect country/continent
info = service.detect_country("DL3TX")
# Returns: {'country': 'Germany', 'continent': 'EU', 'itu_region': 1, 'cq_zone': 14, 'prefix': 'DL'}

# Detect prefix object
prefix = service.detect_prefix("EA8XYZ")
# Returns: CallsignPrefix object with EA8 → Canary Islands

# Detect German license class
license_class = service.detect_german_license_class("DL3TX")
# Returns: "A"
```

### BandService

Located in: `apps/cq/services/band_service.py`

#### Features

- Detect amateur radio band from frequency (database-driven)
- Returns band name (e.g., "40m", "20m", "10m")
- Only uses active band definitions from database

#### Usage Example

```python
from apps.cq.services import BandService

service = BandService()

# Detect band from frequency
band = service.detect_band(7.074)
# Returns: BandDefinition object for 40m

# Get band name directly
band_name = service.get_band_name(14.074)
# Returns: "20m"

# Unknown frequency returns None
band_name = service.get_band_name(999.999)
# Returns: None
```

## Database Models

### CallsignPrefix

Located in: `apps/callsign/models.py`

Maps callsign prefixes to countries, continents, and radio zones.

#### Fields

- `prefix` - Callsign prefix (e.g., "DL", "K", "EA8")
- `country` - Country name
- `continent` - Continent code (e.g., "EU", "NA", "AS")
- `itu_region` - ITU region (1, 2, or 3)
- `cq_zone` - CQ zone number
- `is_active` - Whether this prefix is active (used for lookups)
- `notes` - Additional notes
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

#### Admin Interface

Registered in Django admin with filtering by continent, ITU region, CQ zone, and active status.

### BandDefinition

Located in: `apps/cq/models.py`

Defines amateur radio band frequency ranges.

#### Fields

- `name` - Band name (e.g., "40m", "20m", "10m")
- `lower_frequency_mhz` - Lower frequency bound in MHz
- `upper_frequency_mhz` - Upper frequency bound in MHz
- `mode_hint` - Mode hint (e.g., "HF", "VHF", "UHF")
- `is_active` - Whether this band definition is active (used for lookups)
- `notes` - Additional notes
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

#### Admin Interface

Registered in Django admin with filtering by mode hint and active status.

### GermanCallsignClassRule (Optional)

Located in: `apps/callsign/models.py`

Maps German callsign patterns to license classes.

#### Fields

- `prefix_pattern` - Prefix pattern (e.g., "DO", "DL", "DA6")
- `license_class` - License class (e.g., "A", "E")
- `description` - Description of the license class
- `is_active` - Whether this rule is active (used for lookups)
- `notes` - Additional notes
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

#### Admin Interface

Registered in Django admin with filtering by license class and active status.

## Seed Data

### Loading Initial Data

Use the management command to load initial seed data:

```bash
python manage.py seed_core_data
```

To clear existing data first:

```bash
python manage.py seed_core_data --clear
```

### Included Data

**Band Definitions** (13 bands):
- 160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m, 10m (HF)
- 6m, 2m (VHF)
- 70cm (UHF)

**Callsign Prefixes** (50+ common prefixes):
- German: DL, DA, DB, DC, DD, DF, DG, DH, DJ, DK, DM, DO
- European: OE, HB, F, G, M, 2E, I, IK, IZ, EA, EA8, CT, ON, PA, PD, PE, SP, OM, OK, S5, 9A, E7
- Asian: TA, A6, JA
- Oceania: VK
- North American: K, N, W

**German License Class Rules** (12 patterns):
- Class A: DL, DA, DB, DC, DD, DF, DG, DH, DJ, DK
- Class E: DO, DM

## Algorithm Details

### Prefix Detection

The CallsignService uses a **longest-match algorithm**:

1. Try progressively longer prefixes (from full callsign length down to 1 character)
2. Match against active prefixes in database (case-insensitive)
3. Return the first (longest) match found
4. For portable callsigns, check prefix before slash first

**Examples:**

- `EA8XYZ` matches `EA8` (Canary Islands) before falling back to `EA` (Spain)
- `EA1ABC` matches `EA` (Spain) since `EA1` is not in database
- `DL/AD2LX` matches `DL` (Germany) from prefix before slash

### Band Detection

The BandService uses a **range-based lookup**:

1. Query active BandDefinition records where:
   ```
   lower_frequency_mhz <= frequency_mhz <= upper_frequency_mhz
   ```
2. Return the first matching band (ordered by lower frequency)

**Examples:**

- `7.074 MHz` matches 40m (7.0-7.3 MHz)
- `14.074 MHz` matches 20m (14.0-14.35 MHz)
- `999.999 MHz` returns None (no match)

## Tests

### Running Tests

Run all tests:
```bash
python manage.py test
```

Run specific test classes:
```bash
python manage.py test apps.callsign.tests.CallsignServiceTest
python manage.py test apps.cq.tests.BandServiceTest
```

### Test Coverage

**CallsignService Tests** (20+ tests):
- Normalization (basic, angle brackets, portable, empty)
- QRZ URL generation
- Prefix detection (simple, longest match, unknown, inactive, portable, case-insensitive)
- Country detection
- German license class detection

**BandService Tests** (15+ tests):
- Band detection for various frequencies
- Boundary testing (lower, upper, just outside)
- Inactive band handling
- Invalid frequency handling (None, zero, negative)
- Convenience methods

## Migrations

### Creating Migrations

Migrations have been pre-created for the new models:

- `apps/callsign/migrations/0002_add_fields_and_german_rules.py`
- `apps/cq/migrations/0003_banddefinition.py`

### Applying Migrations

```bash
python manage.py migrate
```

## Integration

### Using in SignalEnricher

The `SignalEnricher` service (in `apps/ingest/services/enrichment.py`) now uses these services:

```python
from apps.callsign.services import CallsignService
from apps.cq.services import BandService

class SignalEnricher:
    def __init__(self, station_lat=None, station_lon=None):
        self.callsign_service = CallsignService()
        self.band_service = BandService()

    def enrich_signal_data(self, signal_data):
        # Use CallsignService for QRZ URL
        enriched['qrz_url'] = self.callsign_service.get_qrz_url(callsign)

        # Use BandService for band detection
        band_name = self.band_service.get_band_name(frequency_mhz)

        # Use CallsignService for country detection
        country_info = self.callsign_service.detect_country(callsign)
```

### Legacy Compatibility

The old `frequency_to_band()` utility function in `apps/geo/utils.py` has been updated to use BandService internally, maintaining backwards compatibility while removing hardcoded data.

## Extending

### Adding New Prefixes

Add prefixes via Django admin or programmatically:

```python
from apps.callsign.models import CallsignPrefix

CallsignPrefix.objects.create(
    prefix='ZL',
    country='New Zealand',
    continent='OC',
    itu_region=3,
    cq_zone=32,
    is_active=True
)
```

### Adding New Bands

Add band definitions via Django admin or programmatically:

```python
from apps.cq.models import BandDefinition

BandDefinition.objects.create(
    name='23cm',
    lower_frequency_mhz=1240.0,
    upper_frequency_mhz=1300.0,
    mode_hint='UHF',
    is_active=True
)
```

### Importing Bulk Data

For bulk imports (e.g., from ALL.TXT or other sources), create a custom management command following the pattern in `seed_core_data.py`.

## Performance Considerations

- Database queries are cached by Django ORM
- Indexes on `prefix`, `is_active`, `lower_frequency_mhz`, `upper_frequency_mhz` ensure fast lookups
- Services are stateless and can be reused across multiple calls
- For high-volume processing, consider instantiating services once and reusing them

## Future Enhancements

Possible future improvements (not in this MVP):

- Import complete CTY.DAT or similar worldwide prefix database
- Auto-update prefix data from online sources
- More sophisticated portable callsign handling
- Full BNetzA German callsign class logic
- Caching layer for frequently-accessed prefixes/bands
- API endpoint for external prefix/band lookups
