# Generated migration for adding station location fields to PropScopeSettings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='propscopesettings',
            name='station_locator',
            field=models.CharField(
                blank=True,
                help_text='Home station Maidenhead locator (4 or 6 characters)',
                max_length=6
            ),
        ),
        migrations.AddField(
            model_name='propscopesettings',
            name='station_latitude',
            field=models.FloatField(
                blank=True,
                help_text='Home station latitude (for distance calculation)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='propscopesettings',
            name='station_longitude',
            field=models.FloatField(
                blank=True,
                help_text='Home station longitude (for distance calculation)',
                null=True
            ),
        ),
    ]
