from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django.conf import settings
import os
import uuid
from pathlib import Path

from django.db.models import Q

from .models import Project, Screen, Component, GenerationLog, GenerationJob
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer,
    ScreenSerializer, ComponentSerializer,
    GenerateFlutterSerializer, LoginSerializer, GenerationJobSerializer
)
from .component_catalog import COMPONENT_CATALOG
from .generators.project_generator import FlutterProjectGenerator
from .utils.apk_builder import APKBuilder
from .utils.preview_server import get_preview_server

from rest_framework.permissions import IsAuthenticated

from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from .jobs import enqueue_project_job, JobRejected

# API endpoints for managing projects


@extend_schema_view(
    generate=extend_schema(responses={202: GenerationJobSerializer}),
    build_apk=extend_schema(responses={202: GenerationJobSerializer}),
    start_preview=extend_schema(responses={202: GenerationJobSerializer}),
)
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.none()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer

    # Override create to return full ProjectSerializer response
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Return full project data with ProjectSerializer
        instance = serializer.instance
        output_serializer = ProjectSerializer(instance)
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # Save project and associate with user
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        project = self.get_object()
        try:
            job = enqueue_project_job(project, 'generate')
        except JobRejected as error:
            return Response({'detail': str(error)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response(GenerationJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        # Download generated Flutter project
        project = self.get_object()

        if not project.generated_file:
            return Response({
                'error': 'Project not generated yet'
            }, status=status.HTTP_404_NOT_FOUND)

        file_path = os.path.join(
            settings.MEDIA_ROOT, project.generated_file.name)

        if not os.path.exists(file_path):
            return Response({
                'error': 'Generated file not found'
            }, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=f"{project.name}.zip"
        )

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        # Get generation logs for a project
        project = self.get_object()
        logs = project.logs.all()

        return Response({
            'logs': [{
                'step': log.step,
                'status': log.status,
                'message': log.message,
                'timestamp': log.timestamp
            } for log in logs]
        })

    @action(detail=True, methods=['post'])
    def build_apk(self, request, pk=None):
        project = self.get_object()

        if not project.generated_file:
            return Response({
                'error': 'Project must be generated first before building APK'
            }, status=status.HTTP_400_BAD_REQUEST)

        if project.status != 'completed':
            return Response({
                'error': 'Project generation must be completed before building APK'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = enqueue_project_job(project, 'build_apk')
        except JobRejected as error:
            return Response({'detail': str(error)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response(GenerationJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def download_apk(self, request, pk=None):
        """Download the built APK file."""
        project = self.get_object()

        if not project.apk_file:
            return Response({
                'error': 'APK not built yet. Please build the APK first.'
            }, status=status.HTTP_404_NOT_FOUND)

        file_path = os.path.join(settings.MEDIA_ROOT, project.apk_file.name)

        if not os.path.exists(file_path):
            return Response({
                'error': 'APK file not found'
            }, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=f"{project.name}.apk"
        )

    @action(detail=True, methods=['post'])
    def start_preview(self, request, pk=None):
        """Queue a live preview server start and return its pollable job."""
        project = self.get_object()

        if not project.generated_file:
            return Response({
                'error': 'Project must be generated first before starting preview'
            }, status=status.HTTP_400_BAD_REQUEST)

        if project.status != 'completed':
            return Response({
                'error': 'Project generation must be completed before starting preview'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = enqueue_project_job(project, 'start_preview')
        except JobRejected as error:
            return Response({'detail': str(error)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response(GenerationJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(operation_id='project_jobs_list', responses={200: GenerationJobSerializer(many=True)})
    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        project = self.get_object()
        jobs = project.jobs.filter(user=request.user)
        return Response(GenerationJobSerializer(jobs, many=True).data)

    @extend_schema(
        operation_id='project_job_status_retrieve',
        parameters=[OpenApiParameter('job_id', OpenApiTypes.UUID, OpenApiParameter.PATH)],
        responses={200: GenerationJobSerializer},
    )
    @action(detail=True, methods=['get'], url_path='jobs/(?P<job_id>[^/.]+)')
    def job_status(self, request, pk=None, job_id=None):
        project = self.get_object()
        job = project.jobs.filter(user=request.user, id=job_id).first()
        if not job:
            return Response({'detail': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(GenerationJobSerializer(job).data)

    @action(detail=True, methods=['get'])
    def preview_status(self, request, pk=None):
        """Return the current launch state for one live preview."""
        project = self.get_object()
        preview_server = get_preview_server()
        result = preview_server.get_preview_status(str(project.id))
        return Response(result)

    @action(detail=True, methods=['post'])
    def stop_preview(self, request, pk=None):
        """Stop the preview server for a project."""
        project = self.get_object()

        try:
            preview_server = get_preview_server()
            success = preview_server.stop_preview(str(project.id))

            if success:
                project.preview_url = None
                project.save()

                GenerationLog.objects.create(
                    project=project,
                    step='preview_stopped',
                    status='success',
                    message='Preview server stopped'
                )

                return Response({
                    'status': 'success',
                    'preview_status': 'stopped',
                    'ready': False,
                    'message': 'Preview server stopped successfully',
                })
            else:
                return Response({
                    'status': 'info',
                    'preview_status': 'stopped',
                    'ready': False,
                    'message': 'No active preview server found for this project',
                })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def update_preview(self, request, pk=None):
        project = self.get_object()

        screen_data = request.data.get('screen')
        if not screen_data:
            return Response({
                'error': 'Request body must include a "screen" object'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            preview_server = get_preview_server()
            result = preview_server.update_screen(
                str(project.id), screen_data)

            return Response({
                'status': 'success',
                'message': f"Hot restarted {result['reloaded_screen']}",
                'reload_mode': result['reload_mode'],
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def preview_heartbeat(self, request, pk=None):
        project = self.get_object()

        preview_server = get_preview_server()
        found = preview_server.touch(str(project.id))

        if not found:
            return Response({
                'status': 'info',
                'message': 'No active preview server found for this project'
            })

        return Response({'status': 'success'})

    @action(detail=False, methods=['get'])
    def active_previews(self, request):
        """Get list of all active preview servers."""
        try:
            preview_server = get_preview_server()
            active_previews = preview_server.get_active_previews()

            return Response({
                'status': 'success',
                'active_previews': active_previews
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# API endpoints for managing screens


class ScreenViewSet(viewsets.ModelViewSet):
    queryset = Screen.objects.none()
    permission_classes = [IsAuthenticated]
    serializer_class = ScreenSerializer

    # Filter screens by project if provided and ensure ownership
    def get_queryset(self):
        queryset = Screen.objects.filter(project__user=self.request.user)
        project_id = self.request.query_params.get('project_id')

        if project_id:
            queryset = queryset.filter(project_id=project_id)

        return queryset

# API endpoints for component library


class ComponentViewSet(viewsets.ModelViewSet):
    queryset = Component.objects.none()
    permission_classes = [IsAuthenticated]
    serializer_class = ComponentSerializer

    def get_queryset(self):
        # The reusable library includes public templates plus the caller's
        # private custom templates.  A custom component never leaks to another
        # account, even if a client submits is_public=true.
        return Component.objects.filter(
            Q(is_public=True) | Q(created_by=self.request.user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            type='custom',
            is_public=False,
        )

    def perform_update(self, serializer):
        if serializer.instance.created_by_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only the owner can edit a custom component.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.created_by_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only the owner can delete a custom component.')
        instance.delete()

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Return every building block the Flutter generator can emit."""
        return Response({'components': COMPONENT_CATALOG})

    @action(detail=False, methods=['get'])
    def categories(self, request):
        categories = sorted({component['category'] for component in COMPONENT_CATALOG})
        return Response({'categories': categories})

# One-time Flutter project generation without saving


class GenerateFlutterView(viewsets.ViewSet):

    @extend_schema(
        request=GenerateFlutterSerializer,
        responses={
            200: {'description': 'A zip file containing the generated Flutter project'}},
        description="Generate a Flutter project directly from a JSON configuration without saving it to the database."
    )
    @action(detail=False, methods=['post'])
    def quick_generate(self, request):
        # Generate Flutter project directly from JSON without saving
        serializer = GenerateFlutterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            json_data = serializer.validated_data.get('json_data')
            project_id = serializer.validated_data.get('project_id')
            if project_id:
                project = Project.objects.filter(id=project_id, user=request.user).first()
                if not project:
                    return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
                json_data = project.json_data
            app_name = serializer.validated_data.get('app_name', 'my_app')
            package_name = serializer.validated_data.get(
                'package_name', 'com.example.myapp')

            # Generate unique output directory
            output_dir = Path(settings.MEDIA_ROOT) / 'temp' / str(uuid.uuid4())
            output_dir.mkdir(parents=True, exist_ok=True)

            generator = FlutterProjectGenerator(
                output_dir=output_dir,
                app_name=app_name,
                package_name=package_name
            )

            zip_path = generator.generate_project(json_data)

            # Return file
            response = FileResponse(
                open(zip_path, 'rb'),
                as_attachment=True,
                filename=f"{app_name}.zip"
            )

            return response

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuthViewSet(viewsets.ViewSet):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @extend_schema(request=UserSerializer)
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=LoginSerializer)
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        # Delete the user's token to log them out
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except (AttributeError, Token.DoesNotExist):
            return Response({'error': 'No active session found'}, status=status.HTTP_400_BAD_REQUEST)
