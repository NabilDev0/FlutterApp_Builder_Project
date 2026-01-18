from rest_framework import serializers
from .models import Project, Screen, Component, GenerationLog
from django.contrib.auth.models import User


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
                  'created_at', 'updated_at', 'generated_file', 'error_message']
        read_only_fields = ['id', 'status',
                            'created_at', 'updated_at', 'generated_file']


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'description', 'json_data']

    # Validate the JSON structure
    def validate_json_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("json_data must be a dictionary")

        if 'screen' not in value and 'screens' not in value:
            raise serializers.ValidationError(
                "json_data must contain 'screen' or 'screens' key")

        return value


class ComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Component
        fields = ['id', 'name', 'type', 'description', 'thumbnail',
                  'template_json', 'is_public', 'created_at']
        read_only_fields = ['id', 'created_at']


class GenerationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerationLog
        fields = ['id', 'step', 'status', 'message', 'timestamp']
        read_only_fields = ['id', 'timestamp']


# Serializer for Flutter project generation request
class GenerateFlutterSerializer(serializers.Serializer):
    project_id = serializers.UUIDField(required=False)
    json_data = serializers.JSONField(required=False)
    app_name = serializers.CharField(max_length=100, required=False)
    package_name = serializers.CharField(max_length=255, required=False)

    def validate(self, data):
        if not data.get('project_id') and not data.get('json_data'):
            raise serializers.ValidationError(
                "Either 'project_id' or 'json_data' must be provided"
            )
        return data

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
