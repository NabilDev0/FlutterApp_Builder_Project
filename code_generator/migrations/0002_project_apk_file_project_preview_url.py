# Generated migration for adding apk_file and preview_url fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('code_generator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='apk_file',
            field=models.FileField(blank=True, null=True, upload_to='apks/'),
        ),
        migrations.AddField(
            model_name='project',
            name='preview_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
