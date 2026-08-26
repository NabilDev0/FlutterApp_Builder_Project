from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('code_generator', '0003_generationjob')]

    operations = [
        migrations.RemoveField(
            model_name='component',
            name='is_public',
        ),
    ]
