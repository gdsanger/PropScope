"""
Django management command to populate auto-detected country and continent fields
in MaidenheadArea records using GeoService.

This command uses Natural Earth shapefile data to automatically detect country
and continent for locators based on their center coordinates.
"""

from django.core.management.base import BaseCommand
from apps.geo.models import MaidenheadArea
from apps.geo.services import GeoService


class Command(BaseCommand):
    help = 'Populate country_auto and continent_auto fields for MaidenheadArea records using GeoService'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-detect for all records, even if they already have auto-detected values'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating'
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        verbosity = options.get('verbosity', 1)

        self.stdout.write(self.style.SUCCESS('=== MaidenheadArea GeoService Auto-Detection ==='))

        if force:
            self.stdout.write(self.style.WARNING('FORCE MODE - Will re-detect for all records'))
        else:
            self.stdout.write('DEFAULT MODE - Will only detect for records without auto-detected values')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Initialize GeoService
        try:
            geo_service = GeoService()
            self.stdout.write(self.style.SUCCESS('✓ GeoService initialized successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to initialize GeoService: {str(e)}'))
            return

        # Get queryset
        qs = MaidenheadArea.objects.all()

        if not force:
            # Only get records without auto-detected values
            qs = qs.filter(country_auto__isnull=True) | qs.filter(continent_auto__isnull=True)

        total_count = qs.count()
        self.stdout.write(f'Records to process: {total_count}')

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No records need auto-detection'))
            return

        # Process records
        updated_count = 0
        skipped_count = 0
        ocean_count = 0

        for area in qs:
            try:
                # Get country and continent from GeoService
                country, continent = geo_service.get_country_continent(
                    area.center_lat,
                    area.center_lon
                )

                if country and continent:
                    # Update fields
                    if not dry_run:
                        area.country_auto = country
                        area.continent_auto = continent
                        area.auto_detected = True
                        area.save(update_fields=['country_auto', 'continent_auto', 'auto_detected'])

                    updated_count += 1

                    if verbosity >= 2:
                        self.stdout.write(
                            f'  ✓ {area.locator}: {country}, {continent}'
                        )
                elif not country and not continent:
                    # Ocean or unmapped area
                    ocean_count += 1
                    if verbosity >= 2:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ~ {area.locator}: No country detected (ocean/unmapped area)'
                            )
                        )
                else:
                    # Partial data
                    skipped_count += 1
                    if verbosity >= 2:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ~ {area.locator}: Partial data (country={country}, continent={continent})'
                            )
                        )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error processing {area.locator}: {str(e)}')
                )
                skipped_count += 1

        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Auto-Detection Complete ==='))
        self.stdout.write(f'Total records processed: {total_count}')
        self.stdout.write(f'Records updated: {updated_count}')
        self.stdout.write(f'Ocean/unmapped areas: {ocean_count}')
        self.stdout.write(f'Records skipped: {skipped_count}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
