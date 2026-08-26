from rest_framework import serializers
from .models import Project, Screen, Component, GenerationLog, GenerationJob
from django.contrib.auth.models import User
from .component_catalog import validate_component_tree, validate_project_tree


class ScreenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screen
        fields = ['id', 'name', 'route', 'is_home',
                  'json_data', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectSerializer(serializers.ModelSerializer):
    screens = ScreenSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'json_data', 'status', 'screens',
                  'created_at', 'updated_at', 'generated_file', 'apk_file', 
                  'preview_url', 'error_message']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at', 
                            'generated_file', 'apk_file', 'preview_url', 'error_message']

    def validate_json_data(self, value):
        error = validate_project_tree(value)
        if error:
            raise serializers.ValidationError(error)
        return value


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'description', 'json_data']

    # Validate the JSON structure
    def validate_json_data(self, value):
        error = validate_project_tree(value)
        if error:
            raise serializers.ValidationError(error)
        return value


class ComponentSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Component
        fields = ['id', 'name', 'type', 'description', 'thumbnail',
                  'template_json', 'created_by', 'created_at']
        read_only_fields = ['id', 'type', 'created_by', 'created_at']

    def validate_template_json(self, value):
        error = validate_component_tree(value)
        if error:
            raise serializers.ValidationError(error)
        return value


class GenerationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerationLog
        fields = ['id', 'step', 'status', 'message', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class GenerationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerationJob
        fields = ['id', 'job_type', 'status', 'error_message', 'result', 'created_at', 'started_at', 'completed_at']
        read_only_fields = fields


# Serializer for Flutter project generation request
class GenerateFlutterSerializer(serializers.Serializer):
    project_id = serializers.UUIDField(required=False)
    json_data = serializers.JSONField(required=False)
    app_name = serializers.CharField(max_length=100, required=False)
    package_name = serializers.CharField(max_length=255, required=False)

    def validate(self, attrs):
        if not attrs.get('project_id') and not attrs.get('json_data'):
            raise serializers.ValidationError(
                "Either 'project_id' or 'json_data' must be provided"
            )
        return attrs

    def validate_json_data(self, value):
        error = validate_project_tree(value)
        if error:
            raise serializers.ValidationError(error)
        return value

    # Validate Android package name format
    def validate_package_name(self, value):
        if value:
            import re
            if not re.match(r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$', value):
                raise serializers.ValidationError(
                    "Invalid package name format. Use format like: com.example.app"
                )
        return value


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
