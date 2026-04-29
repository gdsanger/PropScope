# Generated migration for adding new fields and models

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('callsign', '0001_initial'),
    ]

    operations = [
        # Add new fields to CallsignPrefix
        migrations.AddField(
            model_name='callsignprefix',
            name='is_active',
            field=models.BooleanField(db_index=True, default=True, help_text='Whether this prefix is active and should be used for lookups'),
        ),
        migrations.AddField(
            model_name='callsignprefix',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='callsignprefix',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Add is_active index to CallsignPrefix
        migrations.AddIndex(
            model_name='callsignprefix',
            index=models.Index(fields=['is_active'], name='callsign_ca_is_acti_idx'),
        ),
        # Create GermanCallsignClassRule model
        migrations.CreateModel(
            name='GermanCallsignClassRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prefix_pattern', models.CharField(db_index=True, help_text='Prefix pattern for German callsigns (e.g., DO, DL, DA6)', max_length=20, unique=True)),
                ('license_class', models.CharField(help_text='License class (e.g., A, E)', max_length=10)),
                ('description', models.CharField(blank=True, help_text='Description of the license class or assignment type', max_length=200)),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='Whether this rule is active and should be used for lookups')),
                ('notes', models.TextField(blank=True, help_text='Additional notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'German Callsign Class Rule',
                'verbose_name_plural': 'German Callsign Class Rules',
                'ordering': ['-prefix_pattern'],
                'indexes': [
                    models.Index(fields=['prefix_pattern'], name='callsign_ge_prefix__idx'),
                    models.Index(fields=['is_active'], name='callsign_ge_is_acti_idx'),
                ],
            },
        ),
    ]
