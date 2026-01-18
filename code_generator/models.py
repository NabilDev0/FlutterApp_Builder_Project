from django.db import models
from django.contrib.auth.models import User
import uuid
import os
from django.conf import settings

# Store user projects


class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    json_data = models.JSONField()  # Store the complete screen structure
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_file = models.FileField(
        upload_to='projects/', null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.status}"

    def delete(self, *args, **kwargs):
        # Delete the generated file from storage if it exists
        if self.generated_file:
            # self.generated_file.path provides the full absolute path to the file
            if os.path.isfile(self.generated_file.path):
                os.remove(self.generated_file.path)

        # Call the parent delete method to remove the record from the database
        super().delete(*args, **kwargs)

# Store individual screens


class Screen(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='screens')
    name = models.CharField(max_length=255)
    route = models.CharField(max_length=255)
    is_home = models.BooleanField(default=False)
    json_data = models.JSONField()
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.project.name} - {self.name}"

# Library of reusable components


class Component(models.Model):
    COMPONENT_TYPES = [
        ('widget', 'Basic Widget'),
        ('component', 'Composite Component'),
        ('custom', 'Custom Component'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(
        upload_to='components/', null=True, blank=True)
    template_json = models.JSONField()
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

# Log generation attempts for debugging


class GenerationLog(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='logs')
    step = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.project.name} - {self.step} - {self.status}"
