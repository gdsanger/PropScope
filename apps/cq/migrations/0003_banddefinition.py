# Generated migration for BandDefinition model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cq', '0002_heardsignal_raw_hash'),
    ]

    operations = [
        migrations.CreateModel(
            name='BandDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text='Band name (e.g., 40m, 20m, 10m)', max_length=20, unique=True)),
                ('lower_frequency_mhz', models.FloatField(db_index=True, help_text='Lower frequency bound in MHz')),
                ('upper_frequency_mhz', models.FloatField(db_index=True, help_text='Upper frequency bound in MHz')),
                ('mode_hint', models.CharField(blank=True, help_text='Mode hint (e.g., HF, VHF, UHF)', max_length=20)),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='Whether this band definition is active and should be used for lookups')),
                ('notes', models.TextField(blank=True, help_text='Additional notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Band Definition',
                'verbose_name_plural': 'Band Definitions',
                'ordering': ['lower_frequency_mhz'],
                'indexes': [
                    models.Index(fields=['name'], name='cq_banddefi_name_idx'),
                    models.Index(fields=['lower_frequency_mhz', 'upper_frequency_mhz'], name='cq_banddefi_lower_f_idx'),
                    models.Index(fields=['is_active'], name='cq_banddefi_is_acti_idx'),
                ],
            },
        ),
    ]
