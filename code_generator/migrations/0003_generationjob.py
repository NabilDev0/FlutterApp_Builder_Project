# Generated manually to keep the schema change explicit.
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('code_generator', '0002_project_apk_file_project_preview_url')]

    operations = [
        migrations.CreateModel(
            name='GenerationJob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('job_type', models.CharField(choices=[('generate', 'Generate Flutter project'), ('build_apk', 'Build APK'), ('start_preview', 'Start preview')], max_length=20)),
                ('status', models.CharField(choices=[('queued', 'Queued'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='queued', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('result', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='code_generator.project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generation_jobs', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='generationjob', index=models.Index(fields=['user', 'status'], name='cg_job_user_status_idx')),
        migrations.AddIndex(model_name='generationjob', index=models.Index(fields=['project', 'job_type', 'status'], name='cg_job_project_type_idx')),
    ]
