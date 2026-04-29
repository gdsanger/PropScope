"""
Django management command to poll WSJT-X ALL.TXT file for new entries.
This command is designed to be run periodically via cron.
"""

import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings as django_settings
from apps.ingest.services.wsjtx_importer import WsjtxLogImporter
from apps.ui.models import PropScopeSettings


class Command(BaseCommand):
    help = 'Poll WSJT-X ALL.TXT file for new entries (cron-friendly)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Override file path from settings'
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Minimal output (only errors)'
        )

    def handle(self, *args, **options):
        quiet = options['quiet']

        # Get file path
        file_path = options.get('file')

        if not file_path:
            # Try to get from PropScopeSettings
            try:
                settings = PropScopeSettings.objects.filter(is_active=True).first()
                if settings and settings.wsjtx_all_txt_path:
                    file_path = settings.wsjtx_all_txt_path
                else:
                    # Try environment variable
                    file_path = os.getenv('WSJTX_ALL_TXT_PATH') or django_settings.WSJTX_ALL_TXT_PATH
            except Exception as e:
                raise CommandError(f'Could not get settings: {str(e)}')

        if not file_path:
            raise CommandError(
                'No WSJT-X file path configured. Set it in PropScopeSettings, '
                'WSJTX_ALL_TXT_PATH environment variable, or use --file option.'
            )

        # Check if file exists
        if not os.path.exists(file_path):
            if not quiet:
                self.stdout.write(
                    self.style.WARNING(f'File does not exist yet: {file_path}')
                )
            # Exit gracefully - file may not exist yet
            sys.exit(0)

        # Get settings
        try:
            settings = PropScopeSettings.objects.filter(is_active=True).first()
            if not settings:
                # Create default settings
                settings = PropScopeSettings.objects.create(
                    name='default',
                    wsjtx_all_txt_path=file_path
                )
                if not quiet:
                    self.stdout.write('Created default PropScopeSettings')
        except Exception as e:
            raise CommandError(f'Could not get or create settings: {str(e)}')

        # Run incremental import
        importer = WsjtxLogImporter()

        try:
            import_run = importer.import_file(
                file_path=file_path,
                incremental=True,
                settings=settings
            )

            if not quiet:
                if import_run.lines_imported > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Imported {import_run.lines_imported} new signals '
                            f'(skipped {import_run.lines_skipped})'
                        )
                    )
                else:
                    self.stdout.write('No new signals to import')

            # Exit with status code
            if import_run.status == 'completed':
                sys.exit(0)
            else:
                if not quiet:
                    self.stdout.write(
                        self.style.ERROR(f'Import failed: {import_run.notes}')
                    )
                sys.exit(1)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Import failed: {str(e)}')
            )
            sys.exit(1)
