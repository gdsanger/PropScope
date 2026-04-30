# Generated migration for GeoService auto-detection fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='maidenheadarea',
            name='country_auto',
            field=models.CharField(blank=True, help_text='Country automatically detected from Natural Earth data', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='maidenheadarea',
            name='continent_auto',
            field=models.CharField(blank=True, help_text='Continent automatically detected from Natural Earth data', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='maidenheadarea',
            name='auto_detected',
            field=models.BooleanField(default=False, help_text='True if country_auto and continent_auto were set by GeoService'),
        ),
    ]
