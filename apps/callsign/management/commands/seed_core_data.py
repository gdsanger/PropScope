"""
Management command to seed initial CallsignPrefix and BandDefinition data.

Usage:
    python manage.py seed_core_data
    python manage.py seed_core_data --clear  # Clear existing data first
"""

from django.core.management.base import BaseCommand
from apps.callsign.models import CallsignPrefix, GermanCallsignClassRule
from apps.cq.models import BandDefinition


class Command(BaseCommand):
    help = 'Seed initial CallsignPrefix and BandDefinition data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            CallsignPrefix.objects.all().delete()
            BandDefinition.objects.all().delete()
            GermanCallsignClassRule.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared existing data'))

        # Seed BandDefinition data
        self.stdout.write('\nSeeding BandDefinition data...')
        bands = [
            {'name': '160m', 'lower': 1.8, 'upper': 2.0, 'mode': 'HF'},
            {'name': '80m', 'lower': 3.5, 'upper': 4.0, 'mode': 'HF'},
            {'name': '60m', 'lower': 5.3, 'upper': 5.5, 'mode': 'HF'},
            {'name': '40m', 'lower': 7.0, 'upper': 7.3, 'mode': 'HF'},
            {'name': '30m', 'lower': 10.1, 'upper': 10.15, 'mode': 'HF'},
            {'name': '20m', 'lower': 14.0, 'upper': 14.35, 'mode': 'HF'},
            {'name': '17m', 'lower': 18.068, 'upper': 18.168, 'mode': 'HF'},
            {'name': '15m', 'lower': 21.0, 'upper': 21.45, 'mode': 'HF'},
            {'name': '12m', 'lower': 24.89, 'upper': 24.99, 'mode': 'HF'},
            {'name': '10m', 'lower': 28.0, 'upper': 29.7, 'mode': 'HF'},
            {'name': '6m', 'lower': 50.0, 'upper': 54.0, 'mode': 'VHF'},
            {'name': '2m', 'lower': 144.0, 'upper': 148.0, 'mode': 'VHF'},
            {'name': '70cm', 'lower': 420.0, 'upper': 450.0, 'mode': 'UHF'},
        ]

        for band_data in bands:
            band, created = BandDefinition.objects.get_or_create(
                name=band_data['name'],
                defaults={
                    'lower_frequency_mhz': band_data['lower'],
                    'upper_frequency_mhz': band_data['upper'],
                    'mode_hint': band_data['mode'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  Created: {band.name} ({band.lower_frequency_mhz}-{band.upper_frequency_mhz} MHz)')
            else:
                self.stdout.write(f'  Exists:  {band.name}')

        # Seed CallsignPrefix data
        self.stdout.write('\nSeeding CallsignPrefix data...')
        prefixes = [
            # German prefixes
            {'prefix': 'DL', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DA', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DB', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DC', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DD', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DF', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DG', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DH', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DJ', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DK', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DM', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'DO', 'country': 'Germany', 'continent': 'EU', 'itu': 1, 'cq': 14},
            # Austria
            {'prefix': 'OE', 'country': 'Austria', 'continent': 'EU', 'itu': 1, 'cq': 15},
            # Switzerland
            {'prefix': 'HB', 'country': 'Switzerland', 'continent': 'EU', 'itu': 1, 'cq': 14},
            # France
            {'prefix': 'F', 'country': 'France', 'continent': 'EU', 'itu': 1, 'cq': 14},
            # United Kingdom
            {'prefix': 'G', 'country': 'United Kingdom', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'M', 'country': 'United Kingdom', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': '2E', 'country': 'United Kingdom', 'continent': 'EU', 'itu': 1, 'cq': 14},
            # Italy
            {'prefix': 'I', 'country': 'Italy', 'continent': 'EU', 'itu': 1, 'cq': 15},
            {'prefix': 'IK', 'country': 'Italy', 'continent': 'EU', 'itu': 1, 'cq': 15},
            {'prefix': 'IZ', 'country': 'Italy', 'continent': 'EU', 'itu': 1, 'cq': 15},
            # Spain
            {'prefix': 'EA', 'country': 'Spain', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'EA8', 'country': 'Canary Islands', 'continent': 'AF', 'itu': 1, 'cq': 33},
            # Portugal
            {'prefix': 'CT', 'country': 'Portugal', 'continent': 'EU', 'itu': 1, 'cq': 14},
            # Belgium
            {'prefix': 'ON', 'country': 'Belgium', 'continent': 'EU', 'itu': 1, 'cq': 14},
            # Netherlands
            {'prefix': 'PA', 'country': 'Netherlands', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'PD', 'country': 'Netherlands', 'continent': 'EU', 'itu': 1, 'cq': 14},
            {'prefix': 'PE', 'country': 'Netherlands', 'continent': 'EU', 'itu': 1, 'cq': 14},
            # Poland
            {'prefix': 'SP', 'country': 'Poland', 'continent': 'EU', 'itu': 1, 'cq': 15},
            # Slovakia
            {'prefix': 'OM', 'country': 'Slovakia', 'continent': 'EU', 'itu': 1, 'cq': 15},
            # Czech Republic
            {'prefix': 'OK', 'country': 'Czech Republic', 'continent': 'EU', 'itu': 1, 'cq': 15},
            # Slovenia
            {'prefix': 'S5', 'country': 'Slovenia', 'continent': 'EU', 'itu': 1, 'cq': 15},
            # Croatia
            {'prefix': '9A', 'country': 'Croatia', 'continent': 'EU', 'itu': 1, 'cq': 15},
            # Bosnia
            {'prefix': 'E7', 'country': 'Bosnia and Herzegovina', 'continent': 'EU', 'itu': 1, 'cq': 15},
            # Turkey
            {'prefix': 'TA', 'country': 'Turkey', 'continent': 'AS', 'itu': 1, 'cq': 20},
            # UAE
            {'prefix': 'A6', 'country': 'United Arab Emirates', 'continent': 'AS', 'itu': 1, 'cq': 21},
            # Japan
            {'prefix': 'JA', 'country': 'Japan', 'continent': 'AS', 'itu': 2, 'cq': 25},
            # Australia
            {'prefix': 'VK', 'country': 'Australia', 'continent': 'OC', 'itu': 3, 'cq': 30},
            # USA
            {'prefix': 'K', 'country': 'United States', 'continent': 'NA', 'itu': 2, 'cq': 5},
            {'prefix': 'N', 'country': 'United States', 'continent': 'NA', 'itu': 2, 'cq': 5},
            {'prefix': 'W', 'country': 'United States', 'continent': 'NA', 'itu': 2, 'cq': 5},
        ]

        for prefix_data in prefixes:
            prefix, created = CallsignPrefix.objects.get_or_create(
                prefix=prefix_data['prefix'],
                defaults={
                    'country': prefix_data['country'],
                    'continent': prefix_data['continent'],
                    'itu_region': prefix_data['itu'],
                    'cq_zone': prefix_data['cq'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  Created: {prefix.prefix:4s} → {prefix.country}')
            else:
                self.stdout.write(f'  Exists:  {prefix.prefix:4s} → {prefix.country}')

        # Seed German callsign class rules
        self.stdout.write('\nSeeding GermanCallsignClassRule data...')
        german_rules = [
            {'pattern': 'DO', 'license_class': 'E', 'description': 'Class E'},
            {'pattern': 'DL', 'license_class': 'A', 'description': 'Class A'},
            {'pattern': 'DA', 'license_class': 'A', 'description': 'Class A'},
            {'pattern': 'DB', 'license_class': 'A', 'description': 'Class A (special events)'},
            {'pattern': 'DC', 'license_class': 'A', 'description': 'Class A (special events)'},
            {'pattern': 'DD', 'license_class': 'A', 'description': 'Class A (former GDR)'},
            {'prefix': 'DF', 'license_class': 'A', 'description': 'Class A'},
            {'pattern': 'DG', 'license_class': 'A', 'description': 'Class A (clubs)'},
            {'pattern': 'DH', 'license_class': 'A', 'description': 'Class A'},
            {'pattern': 'DJ', 'license_class': 'A', 'description': 'Class A'},
            {'pattern': 'DK', 'license_class': 'A', 'description': 'Class A'},
            {'pattern': 'DM', 'license_class': 'E', 'description': 'Class E (former Class E/3)'},
        ]

        for rule_data in german_rules:
            # Use 'pattern' if exists, otherwise use 'prefix' (for compatibility)
            pattern = rule_data.get('pattern') or rule_data.get('prefix')
            rule, created = GermanCallsignClassRule.objects.get_or_create(
                prefix_pattern=pattern,
                defaults={
                    'license_class': rule_data['license_class'],
                    'description': rule_data['description'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  Created: {rule.prefix_pattern:4s} → Class {rule.license_class}')
            else:
                self.stdout.write(f'  Exists:  {rule.prefix_pattern:4s} → Class {rule.license_class}')

        self.stdout.write(self.style.SUCCESS('\n✓ Seed data loaded successfully'))
        self.stdout.write(f'  BandDefinitions: {BandDefinition.objects.count()}')
        self.stdout.write(f'  CallsignPrefixes: {CallsignPrefix.objects.count()}')
        self.stdout.write(f'  GermanCallsignClassRules: {GermanCallsignClassRule.objects.count()}')
