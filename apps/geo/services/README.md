# Geo Services

Core services for geographic calculations and Maidenhead locator processing.

## MaidenheadService

A centralized service for Maidenhead locator validation, coordinate conversion, and distance calculations.

### Features

- **Locator Validation**: Validates 4-character and 6-character Maidenhead locators
- **Coordinate Conversion**: Converts locators to latitude/longitude (center of grid square)
- **Distance Calculation**: Haversine formula for accurate great circle distances
- **Error Handling**: Clear exceptions for invalid locators
- **Independent**: No database, UI, or framework dependencies

### Usage

```python
from apps.geo.services import MaidenheadService, InvalidMaidenheadLocatorError

# Create service instance
service = MaidenheadService()

# Normalize and validate a locator
locator = service.normalize_locator(" jn68 ")  # Returns "JN68"
is_valid = service.is_valid_locator("JN68")    # Returns True

# Convert locator to coordinates
lat, lon = service.locator_to_latlon("JN68")  # Returns (48.5, 13.0)

# Calculate distance between coordinates
distance = service.distance_km(48.5, 13.0, 51.5, 5.0)  # Returns distance in km

# Calculate distance between locators
distance = service.distance_between_locators("JN68", "JO21")  # Returns ~661.5 km

# Handle invalid locators
try:
    service.locator_to_latlon("ZZ99")  # Invalid locator
except InvalidMaidenheadLocatorError as e:
    print(f"Error: {e}")
```

### Supported Locator Formats

#### 4-Character Locators (Primary)
- Format: `[A-R][A-R][0-9][0-9]`
- Examples: `JN68`, `JO21`, `MN72`
- Precision: ~110 km × 55 km grid square

#### 6-Character Locators (Optional)
- Format: `[A-R][A-R][0-9][0-9][A-X][A-X]`
- Examples: `JN68qv`, `JN58aa`
- Precision: ~5 km × 2.5 km subsquare

### API Reference

#### `normalize_locator(locator: str) -> str`
Normalizes a locator by stripping whitespace and converting to uppercase.

**Parameters:**
- `locator`: Raw locator string

**Returns:**
- Normalized locator string

**Example:**
```python
service.normalize_locator(" jn68 ")  # Returns "JN68"
```

#### `is_valid_locator(locator: str) -> bool`
Validates a Maidenhead locator format.

**Parameters:**
- `locator`: Locator string to validate

**Returns:**
- `True` if valid, `False` otherwise

**Example:**
```python
service.is_valid_locator("JN68")  # Returns True
service.is_valid_locator("ZZ99")  # Returns False
```

#### `locator_to_latlon(locator: str) -> Tuple[float, float]`
Converts a Maidenhead locator to latitude/longitude coordinates (center of grid square).

**Parameters:**
- `locator`: Maidenhead locator string (4 or 6 characters)

**Returns:**
- Tuple of `(latitude, longitude)` in degrees

**Raises:**
- `InvalidMaidenheadLocatorError`: If locator format is invalid

**Example:**
```python
lat, lon = service.locator_to_latlon("JN68")  # Returns (48.5, 13.0)
```

#### `distance_km(from_lat: float, from_lon: float, to_lat: float, to_lon: float) -> float`
Calculates the great circle distance between two points using the Haversine formula.

**Parameters:**
- `from_lat`: Latitude of first point in degrees
- `from_lon`: Longitude of first point in degrees
- `to_lat`: Latitude of second point in degrees
- `to_lon`: Longitude of second point in degrees

**Returns:**
- Distance in kilometers

**Example:**
```python
distance = service.distance_km(48.78, 9.18, 48.14, 11.58)  # ~190.7 km
```

#### `distance_between_locators(from_locator: str, to_locator: str) -> float`
Calculates the distance between two Maidenhead locators.

**Parameters:**
- `from_locator`: First Maidenhead locator
- `to_locator`: Second Maidenhead locator

**Returns:**
- Distance in kilometers

**Raises:**
- `InvalidMaidenheadLocatorError`: If either locator is invalid

**Example:**
```python
distance = service.distance_between_locators("JN68", "JO21")  # ~661.5 km
```

### Exceptions

#### `InvalidMaidenheadLocatorError`
Raised when a Maidenhead locator is invalid or malformed.

**Base Class:** `ValueError`

**Example:**
```python
try:
    service.locator_to_latlon("INVALID")
except InvalidMaidenheadLocatorError as e:
    print(f"Invalid locator: {e}")
```

### Testing

The service includes comprehensive unit tests covering:
- Locator normalization
- Locator validation (valid and invalid cases)
- Coordinate conversion (4-char and 6-char locators)
- Distance calculations
- Error handling
- Edge cases and boundaries

**Run tests:**
```bash
# Standalone tests (no database required)
python test_maidenhead_service.py

# Django tests (requires database)
python manage.py test apps.geo.tests.MaidenheadServiceTests
```

### Examples

See `example_maidenhead_service.py` in the project root for complete usage examples.

### Design Principles

1. **Independence**: No dependencies on Django models, database, or UI
2. **Reusability**: Can be used by importers, statistics, and UI components
3. **Type Safety**: Full type hints for all methods
4. **Error Handling**: Clear exceptions for invalid inputs
5. **Stateless**: Service instances are stateless and thread-safe
6. **Standards Compliant**: Follows standard Maidenhead grid square system

### Maidenhead Grid System

The Maidenhead Locator System divides the world into a hierarchical grid:

1. **Field (2 letters)**: 18 × 18 fields covering the globe
   - Each field: 20° longitude × 10° latitude
   - Example: `JN`

2. **Square (2 digits)**: 10 × 10 squares per field
   - Each square: 2° longitude × 1° latitude
   - Example: `68`

3. **Subsquare (2 letters, optional)**: 24 × 24 subsquares per square
   - Each subsquare: ~5 km × 2.5 km
   - Example: `qv`

The service returns the **center point** of each grid square for consistent distance calculations.

### Performance Considerations

- All calculations use standard Python `math` library (very fast)
- No database queries or external API calls
- Stateless design allows for easy caching if needed
- Typical operation: < 1ms per calculation

### Future Enhancements

Potential future additions (not required for MVP):
- Reverse geocoding (coordinates to locator)
- Distance with azimuth/bearing
- Grid square boundary calculations
- Batch conversion operations
- Extended precision (8-character locators)
