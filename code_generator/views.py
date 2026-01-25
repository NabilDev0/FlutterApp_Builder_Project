from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django.conf import settings
import os
import uuid
from pathlib import Path

from .models import Project, Screen, Component, GenerationLog
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer,
    ScreenSerializer, ComponentSerializer,
    GenerateFlutterSerializer, LoginSerializer
)
from .generators.project_generator import FlutterProjectGenerator
from .utils.apk_builder import APKBuilder
from .utils.preview_server import get_preview_server

from rest_framework.permissions import IsAuthenticated

from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from .serializers import UserSerializer

# API endpoints for managing projects


class ProjectViewSet(viewsets.ModelViewSet):
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
        # Generate Flutter project from saved project
        project = self.get_object()

        # Update status
        project.status = 'generating'
        project.save()

        try:
            # Create log
            GenerationLog.objects.create(
                project=project,
                step='start',
                status='info',
                message='Starting project generation'
            )

            # Generate project
            output_dir = Path(settings.MEDIA_ROOT) / 'projects'
            output_dir.mkdir(parents=True, exist_ok=True)

            app_name = project.name.lower().replace(' ', '_')
            package_name = f"com.example.{app_name}"

            generator = FlutterProjectGenerator(
                output_dir=output_dir,
                app_name=app_name,
                package_name=package_name
            )

            GenerationLog.objects.create(
                project=project,
                step='generate_structure',
                status='info',
                message='Generating project structure'
            )

            zip_path = generator.generate_project(project.json_data)

            # Save zip file reference
            relative_path = os.path.relpath(zip_path, settings.MEDIA_ROOT)
            project.generated_file = relative_path
            project.status = 'completed'
            project.save()

            GenerationLog.objects.create(
                project=project,
                step='complete',
                status='success',
                message='Project generated successfully'
            )

            return Response({
                'status': 'success',
                'message': 'Project generated successfully',
                'download_url': f'/api/projects/{project.id}/download/'
            })

        except Exception as e:
            project.status = 'failed'
            project.error_message = str(e)
            project.save()

            GenerationLog.objects.create(
                project=project,
                step='error',
                status='error',
                message=str(e)
            )

            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

        # Store original status to restore on error
        original_status = project.status
        project.status = 'generating'
        project.save()

        try:
            GenerationLog.objects.create(
                project=project,
                step='build_apk_start',
                status='info',
                message='Starting APK build process'
            )

            # Get the ZIP file path
            zip_path = os.path.join(
                settings.MEDIA_ROOT, project.generated_file.name)

            # Build APK
            apk_output_dir = Path(settings.MEDIA_ROOT) / 'apks'
            apk_output_dir.mkdir(parents=True, exist_ok=True)

            builder = APKBuilder()
            apk_path = builder.build_apk_from_zip(zip_path, apk_output_dir)

            # Save APK file reference
            relative_path = os.path.relpath(apk_path, settings.MEDIA_ROOT)
            project.apk_file = relative_path
            project.status = 'completed'
            project.save()

            GenerationLog.objects.create(
                project=project,
                step='build_apk_complete',
                status='success',
                message='APK built successfully'
            )

            return Response({
                'status': 'success',
                'message': 'APK built successfully',
                'download_url': f'/api/projects/{project.id}/download_apk/'
            })

        except Exception as e:
            # Restore original status - APK build failure shouldn't affect project generation status
            project.status = original_status
            project.error_message = str(e)
            project.save()

            GenerationLog.objects.create(
                project=project,
                step='build_apk_error',
                status='error',
                message=str(e)
            )

            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        """Start a live preview server for the generated Flutter project."""
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
            GenerationLog.objects.create(
                project=project,
                step='preview_start',
                status='info',
                message='Starting preview server'
            )

            # Get the ZIP file path
            zip_path = os.path.join(
                settings.MEDIA_ROOT, project.generated_file.name)

            # Create temporary directory for preview
            import tempfile
            temp_dir = Path(settings.MEDIA_ROOT) / 'previews' / str(project.id)
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Start preview server
            preview_server = get_preview_server()
            result = preview_server.preview_from_zip(
                zip_path, temp_dir, project_id=str(project.id))

            # Save preview URL
            project.preview_url = result['preview_url']
            project.save()

            GenerationLog.objects.create(
                project=project,
                step='preview_started',
                status='success',
                message=f"Preview server started at {result['preview_url']}"
            )

            return Response({
                'status': 'success',
                'message': 'Preview server started successfully',
                'preview_url': result['preview_url'],
                'port': result['port']
            })

        except Exception as e:
            GenerationLog.objects.create(
                project=project,
                step='preview_error',
                status='error',
                message=str(e)
            )

            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                    'message': 'Preview server stopped successfully'
                })
            else:
                return Response({
                    'status': 'info',
                    'message': 'No active preview server found for this project'
                })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    queryset = Component.objects.filter(is_public=True)
    serializer_class = ComponentSerializer

    @action(detail=False, methods=['get'])
    def categories(self, request):
        # Get component categories
        categories = Component.objects.values_list(
            'type', flat=True).distinct()
        return Response({'categories': list(categories)})

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
