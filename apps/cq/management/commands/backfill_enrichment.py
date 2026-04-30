"""
Django management command to backfill missing enrichment data for HeardSignal records.

This command re-enriches HeardSignal records that are missing enrichment fields such as:
- qrz_url
- band
- distance_km
- callsign_country, callsign_continent
- locator_country, locator_continent, locator_ambiguous
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.cq.models import HeardSignal
from apps.ui.models import PropScopeSettings, StationProfile
from apps.ingest.services.enrichment import SignalEnricher


class Command(BaseCommand):
    help = 'Backfill missing enrichment data for HeardSignal records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch (default: 1000)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of records to process (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-enrich all records, even if they already have enrichment data (legacy alias for --full)'
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Full rebuild: Re-enrich all records, overwriting existing enrichment data'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        limit = options.get('limit')
        dry_run = options['dry_run']
        force = options['force']
        full = options['full']
        # Store verbosity from options for use throughout the command
        self.verbosity = options.get('verbosity', 1)

        # --full and --force are aliases; use either one
        full_rebuild = full or force

        self.stdout.write(self.style.SUCCESS('=== HeardSignal Enrichment Backfill ==='))

        if full_rebuild:
            self.stdout.write(self.style.WARNING('FULL REBUILD MODE - Will re-enrich all records, overwriting existing data'))
        else:
            self.stdout.write('DEFAULT MODE - Will only enrich records with missing data')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Get station coordinates from settings
        settings = PropScopeSettings.objects.filter(is_active=True).first()
        station_lat = settings.station_latitude if settings else None
        station_lon = settings.station_longitude if settings else None
        coordinate_source = None

        # If no coordinates in settings, try to get from default StationProfile
        if not (station_lat and station_lon):
            station_profile = StationProfile.objects.filter(is_default=True, is_active=True).first()
            if station_profile:
                station_lat = station_profile.latitude
                station_lon = station_profile.longitude
                if station_lat and station_lon:
                    coordinate_source = f"StationProfile '{station_profile.name}'"
        else:
            coordinate_source = "PropScopeSettings"

        if station_lat and station_lon:
            self.stdout.write(f'Station coordinates: {station_lat}, {station_lon} (from {coordinate_source})')
        else:
            self.stdout.write(self.style.WARNING('No station coordinates found - distance calculation will be skipped'))

        # Create enricher
        enricher = SignalEnricher(station_lat=station_lat, station_lon=station_lon)

        # Build queryset
        qs = HeardSignal.objects.all()

        if not full_rebuild:
            # Only get records missing enrichment data
            qs = qs.filter(
                qrz_url__isnull=True
            ) | qs.filter(
                band=''
            ) | qs.filter(
                callsign_country__isnull=True
            ) | qs.filter(
                locator_country__isnull=True,
                locator__isnull=False
            )

        if limit:
            qs = qs[:limit]

        total_count = qs.count()
        self.stdout.write(f'Records to process: {total_count}')

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No records need backfilling'))
            return

        # Process in batches
        updated_count = 0
        skipped_count = 0
        batch_start = 0

        while batch_start < total_count:
            batch_end = min(batch_start + batch_size, total_count)
            batch = list(qs[batch_start:batch_end])

            self.stdout.write(f'\nProcessing batch {batch_start + 1}-{batch_end} of {total_count}...')

            for signal in batch:
                try:
                    # Prepare signal data
                    signal_data = {
                        'callsign': signal.callsign,
                        'locator': signal.locator,
                        'frequency_mhz': signal.frequency_mhz,
                    }

                    # Enrich the data
                    enriched = enricher.enrich_signal_data(signal_data)

                    # Check if any field would be updated
                    updates_needed = False
                    updates = {}

                    # QRZ URL
                    if enriched.get('qrz_url'):
                        if full_rebuild or not signal.qrz_url:
                            updates['qrz_url'] = enriched['qrz_url']
                            updates_needed = True

                    # Band
                    if enriched.get('band'):
                        if full_rebuild or not signal.band or signal.band == '':
                            updates['band'] = enriched['band']
                            updates_needed = True

                    # Distance
                    if enriched.get('distance_km'):
                        if full_rebuild or signal.distance_km is None:
                            updates['distance_km'] = enriched['distance_km']
                            updates_needed = True

                    # Callsign country/continent
                    if enriched.get('callsign_country'):
                        if full_rebuild or not signal.callsign_country:
                            updates['callsign_country'] = enriched['callsign_country']
                            updates_needed = True
                    if enriched.get('callsign_continent'):
                        if full_rebuild or not signal.callsign_continent:
                            updates['callsign_continent'] = enriched['callsign_continent']
                            updates_needed = True

                    # Locator enrichment
                    if signal.locator:
                        if enriched.get('locator_country'):
                            if full_rebuild or not signal.locator_country:
                                updates['locator_country'] = enriched['locator_country']
                                updates_needed = True
                        if enriched.get('locator_alt_country'):
                            if full_rebuild or not signal.locator_alt_country:
                                updates['locator_alt_country'] = enriched['locator_alt_country']
                                updates_needed = True
                        if enriched.get('locator_continent'):
                            if full_rebuild or not signal.locator_continent:
                                updates['locator_continent'] = enriched['locator_continent']
                                updates_needed = True
                        if enriched.get('locator_ambiguous') is not None:
                            if full_rebuild or signal.locator_ambiguous is None:
                                updates['locator_ambiguous'] = enriched['locator_ambiguous']
                                updates_needed = True
                        if enriched.get('locator_lat'):
                            if full_rebuild or signal.locator_lat is None:
                                updates['locator_lat'] = enriched['locator_lat']
                                updates_needed = True
                        if enriched.get('locator_lon'):
                            if full_rebuild or signal.locator_lon is None:
                                updates['locator_lon'] = enriched['locator_lon']
                                updates_needed = True

                    if updates_needed:
                        if not dry_run:
                            # Update the signal
                            for field, value in updates.items():
                                setattr(signal, field, value)
                            signal.save(update_fields=list(updates.keys()))

                        updated_count += 1

                        if self.verbosity >= 2:
                            self.stdout.write(f'  Updated {signal.callsign} ({signal.id}): {", ".join(updates.keys())}')
                    else:
                        skipped_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Error processing signal {signal.id}: {str(e)}')
                    )
                    skipped_count += 1

            batch_start = batch_end

        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Backfill Complete ==='))
        self.stdout.write(f'Total records processed: {total_count}')
        self.stdout.write(f'Records updated: {updated_count}')
        self.stdout.write(f'Records skipped: {skipped_count}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
