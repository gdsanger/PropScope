"""
WSJT-X ALL.TXT log importer service.
Main service for importing and processing WSJT-X log files.
"""

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from django.db import transaction, IntegrityError
from apps.ingest.models import ImportRun
from apps.cq.models import HeardSignal
from apps.ui.models import PropScopeSettings, StationProfile
from apps.ingest.services.parser import WsjtxLineParser
from apps.ingest.services.enrichment import SignalEnricher


logger = logging.getLogger(__name__)


class WsjtxLogImporter:
    """
    Service for importing WSJT-X ALL.TXT log files.
    """

    def __init__(self):
        self.parser = WsjtxLineParser()

    def import_file(
        self,
        file_path: str,
        incremental: bool = True,
        settings: Optional[PropScopeSettings] = None
    ) -> ImportRun:
        """
        Import a WSJT-X ALL.TXT file.

        Args:
            file_path: Path to the ALL.TXT file
            incremental: If True, only import new lines since last position
            settings: PropScopeSettings instance for station location and tracking

        Returns:
            ImportRun instance with import statistics
        """
        # Get settings if not provided
        if settings is None:
            try:
                settings = PropScopeSettings.objects.filter(is_active=True).first()
            except PropScopeSettings.DoesNotExist:
                settings = None

        # Create enricher with station coordinates
        station_lat = settings.station_latitude if settings else None
        station_lon = settings.station_longitude if settings else None

        # If no coordinates in settings, try to get from default StationProfile
        if not (station_lat and station_lon):
            station_profile = StationProfile.objects.filter(is_default=True, is_active=True).first()
            if station_profile:
                station_lat = station_profile.latitude
                station_lon = station_profile.longitude

        enricher = SignalEnricher(station_lat=station_lat, station_lon=station_lon)

        # Create import run
        import_run = ImportRun.objects.create(
            source_filename=file_path,
            status='running'
        )

        # Determine starting position
        start_position = 0
        if incremental and settings and settings.wsjtx_last_position > 0:
            start_position = settings.wsjtx_last_position

        try:
            # Import the file
            stats = self._process_file(
                file_path=file_path,
                import_run=import_run,
                enricher=enricher,
                start_position=start_position
            )

            # Update import run with results
            import_run.lines_total = stats['lines_total']
            import_run.lines_imported = stats['lines_imported']
            import_run.lines_skipped = stats['lines_skipped']
            import_run.status = 'completed'
            import_run.finished_at = datetime.now(timezone.utc)

            # Update last position in settings if incremental
            if incremental and settings:
                settings.wsjtx_last_position = stats['file_position']
                settings.save(update_fields=['wsjtx_last_position'])

        except Exception as e:
            import_run.status = 'failed'
            import_run.notes = f"Import failed: {str(e)}"
            import_run.finished_at = datetime.now(timezone.utc)
            raise
        finally:
            import_run.save()

        return import_run

    def _process_file(
        self,
        file_path: str,
        import_run: ImportRun,
        enricher: SignalEnricher,
        start_position: int = 0
    ) -> dict:
        """
        Process the file and import CQ signals.

        Args:
            file_path: Path to the file
            import_run: ImportRun instance
            enricher: SignalEnricher instance
            start_position: Byte position to start reading from

        Returns:
            Dictionary with import statistics
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        lines_total = 0
        lines_imported = 0
        lines_skipped = 0
        current_position = start_position

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            # Seek to start position if incremental
            if start_position > 0:
                f.seek(start_position)

            while True:
                line = f.readline()
                if not line:
                    # End of file
                    break

                lines_total += 1

                # Update position after reading
                current_position = f.tell()

                # Skip empty lines
                if not line.strip():
                    lines_skipped += 1
                    continue

                # Quick check: skip non-CQ lines
                if not self.parser.is_cq_line(line):
                    lines_skipped += 1
                    continue

                # Parse the line
                parsed = self.parser.parse_line(line)
                if not parsed or not parsed.is_cq:
                    lines_skipped += 1
                    continue

                # Import the signal
                success = self._import_signal(parsed, import_run, enricher)
                if success:
                    lines_imported += 1
                else:
                    lines_skipped += 1

        return {
            'lines_total': lines_total,
            'lines_imported': lines_imported,
            'lines_skipped': lines_skipped,
            'file_position': current_position
        }

    def _import_signal(
        self,
        parsed,
        import_run: ImportRun,
        enricher: SignalEnricher
    ) -> bool:
        """
        Import a single parsed signal into the database.

        Args:
            parsed: ParsedWsjtxLine instance
            import_run: ImportRun instance
            enricher: SignalEnricher instance

        Returns:
            True if imported successfully, False if skipped (duplicate or error)
        """
        # Calculate hash for deduplication
        raw_hash = hashlib.sha256(parsed.raw_line.encode('utf-8')).hexdigest()

        # Check if already exists
        if HeardSignal.objects.filter(raw_hash=raw_hash).exists():
            return False

        # Prepare signal data
        signal_data = {
            'callsign': parsed.callsign,
            'locator': parsed.locator,
            'frequency_mhz': parsed.frequency_mhz,
        }

        # Enrich the data
        try:
            enriched = enricher.enrich_signal_data(signal_data)
        except Exception as e:
            # Log enrichment error but continue
            logger.error(f"Enrichment failed for signal {parsed.callsign}: {e}", exc_info=True)
            # Use unenriched data
            enriched = signal_data

        # Create HeardSignal
        try:
            with transaction.atomic():
                HeardSignal.objects.create(
                    import_run=import_run,
                    timestamp=parsed.timestamp,
                    frequency_mhz=parsed.frequency_mhz,
                    band=enriched.get('band', ''),
                    mode=parsed.mode,
                    snr=parsed.snr,
                    dt=parsed.dt,
                    audio_frequency=parsed.audio_frequency,
                    raw_message=parsed.message,
                    raw_line=parsed.raw_line,
                    raw_hash=raw_hash,
                    callsign=parsed.callsign or '',
                    callsign_country=enriched.get('callsign_country'),
                    callsign_continent=enriched.get('callsign_continent'),
                    qrz_url=enriched.get('qrz_url'),
                    cq_target=parsed.cq_target,
                    locator=enriched.get('locator'),  # Use enriched locator (may be None if invalid)
                    locator_lat=enriched.get('locator_lat'),
                    locator_lon=enriched.get('locator_lon'),
                    locator_country=enriched.get('locator_country'),
                    locator_alt_country=enriched.get('locator_alt_country'),
                    locator_continent=enriched.get('locator_continent'),
                    locator_ambiguous=enriched.get('locator_ambiguous', False),
                    distance_km=enriched.get('distance_km'),
                    azimuth_deg=enriched.get('azimuth_deg')
                )
            return True
        except IntegrityError:
            # Duplicate entry (race condition)
            return False
        except Exception as e:
            # Log database error and skip this signal
            logger.error(f"Import failed for signal {parsed.callsign} at {parsed.timestamp}: {e}", exc_info=True)
            return False
