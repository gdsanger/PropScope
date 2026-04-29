# Generated migration for adding raw_hash field to HeardSignal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cq', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='heardsignal',
            name='raw_hash',
            field=models.CharField(
                db_index=True,
                default='',
                help_text='SHA256 hash of raw_line for deduplication',
                max_length=64,
                unique=True
            ),
            preserve_default=False,
        ),
    ]
