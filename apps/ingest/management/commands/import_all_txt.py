"""
Django management command to import WSJT-X ALL.TXT files.
"""

from django.core.management.base import BaseCommand, CommandError
from apps.ingest.services.wsjtx_importer import WsjtxLogImporter
from apps.ui.models import PropScopeSettings


class Command(BaseCommand):
    help = 'Import WSJT-X ALL.TXT log file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to the WSJT-X ALL.TXT file'
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Import entire file (ignore last position)'
        )
        parser.add_argument(
            '--incremental',
            action='store_true',
            help='Import only new lines since last position (default)'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        incremental = not options['full']  # Default to incremental unless --full

        self.stdout.write(
            self.style.SUCCESS(f'Starting import of: {file_path}')
        )

        if incremental:
            self.stdout.write('Mode: Incremental (only new lines)')
        else:
            self.stdout.write('Mode: Full import')

        # Get settings
        try:
            settings = PropScopeSettings.objects.filter(is_active=True).first()
            if settings:
                self.stdout.write(f'Using settings: {settings.name}')
                if settings.station_locator:
                    self.stdout.write(f'Station locator: {settings.station_locator}')
        except Exception:
            settings = None
            self.stdout.write(
                self.style.WARNING('No active PropScopeSettings found')
            )

        # Run import
        importer = WsjtxLogImporter()

        try:
            import_run = importer.import_file(
                file_path=file_path,
                incremental=incremental,
                settings=settings
            )

            # Display results
            self.stdout.write(self.style.SUCCESS('\n=== Import Complete ==='))
            self.stdout.write(f'Status: {import_run.status}')
            self.stdout.write(f'Lines processed: {import_run.lines_total}')
            self.stdout.write(f'Lines imported: {import_run.lines_imported}')
            self.stdout.write(f'Lines skipped: {import_run.lines_skipped}')

            if import_run.notes:
                self.stdout.write(f'Notes: {import_run.notes}')

            if import_run.status == 'completed':
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nSuccessfully imported {import_run.lines_imported} signals'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'\nImport failed: {import_run.notes}')
                )

        except FileNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Import failed: {str(e)}')
