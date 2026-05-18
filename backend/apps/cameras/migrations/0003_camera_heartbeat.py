# Generated migration for camera heartbeat

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cameras', '0002_camera_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='camera',
            name='last_heartbeat',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='camera',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
