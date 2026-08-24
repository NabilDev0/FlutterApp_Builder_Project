"""Bounded background execution for expensive Flutter operations.

The database is the job-status source of truth.  The thread runner is suitable
for this single-process deployment; its public enqueue API deliberately keeps
the execution backend replaceable by Celery/RQ later.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from .generators.project_generator import FlutterProjectGenerator
from .component_catalog import validate_project_tree
from .models import GenerationJob, GenerationLog, Project
from .utils.apk_builder import APKBuilder
from .utils.preview_server import get_preview_server


class JobRejected(Exception):
    pass


_executor = ThreadPoolExecutor(
    max_workers=getattr(settings, 'BACKGROUND_JOB_MAX_WORKERS', 2),
    thread_name_prefix='flutter-job',
)


def enqueue_project_job(project, job_type):
    """Create a job only when the user has remaining queue capacity."""
    with transaction.atomic():
        # Locking the user row serializes the first enqueue too, when there are
        # no existing job rows available to lock yet.
        get_user_model().objects.select_for_update().get(pk=project.user_id)
        active = GenerationJob.objects.select_for_update().filter(
            user=project.user, status__in=['queued', 'running']
        )
        if active.filter(status='running').count() >= settings.MAX_ACTIVE_JOBS_PER_USER:
            raise JobRejected('You already have the maximum number of running jobs.')
        if active.count() >= settings.MAX_QUEUED_JOBS_PER_USER:
            raise JobRejected('You already have the maximum number of queued jobs.')
        if active.filter(project=project, job_type=job_type).exists():
            raise JobRejected(f'A {job_type} job is already queued or running for this project.')
        job = GenerationJob.objects.create(project=project, user=project.user, job_type=job_type)

    _executor.submit(run_job, str(job.id))
    return job


def run_job(job_id):
    """Run one job, persisting every terminal state for polling clients."""
    with transaction.atomic():
        job = GenerationJob.objects.select_for_update().select_related('project').get(id=job_id)
        if job.status != 'queued':
            return
        job.status = 'running'
        job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at'])

    try:
        if job.job_type == 'generate':
            result = _generate(job)
        elif job.job_type == 'build_apk':
            result = _build_apk(job)
        elif job.job_type == 'start_preview':
            result = _start_preview(job)
        else:
            raise ValueError(f'Unsupported job type: {job.job_type}')
    except Exception as error:
        _fail(job, str(error))
        return

    GenerationJob.objects.filter(id=job.id).update(
        status='completed', result=result, completed_at=timezone.now(), error_message=''
    )


def _project_app_name(project):
    # Flutter package names must be lower snake case.  Project IDs make output
    # paths unique; this name is only used inside the generated archive.
    import re
    name = re.sub(r'[^a-z0-9_]+', '_', project.name.lower()).strip('_')
    if not name or not name[0].isalpha():
        name = f'app_{name}'
    return name[:80]


def _generate(job):
    project = Project.objects.get(id=job.project_id)
    validation_error = validate_project_tree(project.json_data)
    if validation_error:
        raise ValueError(validation_error)
    project.status = 'generating'
    project.error_message = ''
    project.save(update_fields=['status', 'error_message', 'updated_at'])
    GenerationLog.objects.create(project=project, step='generate_structure', status='info', message='Generating project structure')

    app_name = _project_app_name(project)
    output_dir = Path(settings.MEDIA_ROOT) / 'projects' / str(project.id) / str(job.id)
    zip_path = FlutterProjectGenerator(
        output_dir=output_dir,
        app_name=app_name,
        package_name=f'com.example.{app_name}',
    ).generate_project(project.json_data)
    relative_path = os.path.relpath(zip_path, settings.MEDIA_ROOT)
    previous_file = project.generated_file.name if project.generated_file else None
    project.generated_file = relative_path
    project.status = 'completed'
    project.save(update_fields=['generated_file', 'status', 'updated_at'])
    if previous_file and previous_file != relative_path and default_storage.exists(previous_file):
        default_storage.delete(previous_file)
    GenerationLog.objects.create(project=project, step='complete', status='success', message='Project generated successfully')
    return {'download_url': f'/api/projects/{project.id}/download/'}


def _build_apk(job):
    project = Project.objects.get(id=job.project_id)
    if not project.generated_file:
        raise ValueError('Project must be generated before building an APK.')
    source_zip = Path(settings.MEDIA_ROOT) / project.generated_file.name
    output_dir = Path(settings.MEDIA_ROOT) / 'apks' / str(project.id) / str(job.id)
    GenerationLog.objects.create(project=project, step='build_apk_start', status='info', message='Starting APK build process')
    apk_path = APKBuilder().build_apk_from_zip(source_zip, output_dir)
    relative_path = os.path.relpath(apk_path, settings.MEDIA_ROOT)
    previous_file = project.apk_file.name if project.apk_file else None
    project.apk_file = relative_path
    project.save(update_fields=['apk_file', 'updated_at'])
    if previous_file and previous_file != relative_path and default_storage.exists(previous_file):
        default_storage.delete(previous_file)
    GenerationLog.objects.create(project=project, step='build_apk_complete', status='success', message='APK built successfully')
    return {'download_url': f'/api/projects/{project.id}/download_apk/'}


def _start_preview(job):
    project = Project.objects.get(id=job.project_id)
    if not project.generated_file:
        raise ValueError('Project must be generated before starting a preview.')
    GenerationLog.objects.create(project=project, step='preview_start', status='info', message='Starting preview server')
    zip_path = Path(settings.MEDIA_ROOT) / project.generated_file.name
    temp_dir = Path(settings.MEDIA_ROOT) / 'previews' / str(project.id)
    result = get_preview_server().preview_from_zip(zip_path, temp_dir, project_id=str(project.id))
    project.preview_url = result['preview_url']
    project.save(update_fields=['preview_url', 'updated_at'])
    GenerationLog.objects.create(project=project, step='preview_started', status='success', message=f"Preview server started at {result['preview_url']}")
    return {'preview_url': result['preview_url'], 'preview_status': result['preview_status'], 'ready': result['ready'], 'port': result['port']}


def _fail(job, message):
    job = GenerationJob.objects.select_related('project').get(id=job.id)
    if job.job_type == 'generate':
        Project.objects.filter(id=job.project_id).update(status='failed', error_message=message, updated_at=timezone.now())
    GenerationLog.objects.create(project=job.project, step=f'{job.job_type}_error', status='error', message=message)
    GenerationJob.objects.filter(id=job.id).update(status='failed', error_message=message, completed_at=timezone.now())
