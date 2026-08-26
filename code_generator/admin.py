from django.contrib import admin
from .models import Project, Screen, Component, GenerationLog


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'name', 'description', 'status')
        }),
        ('Project Data', {
            'fields': ('json_data',),
            'classes': ('collapse',)
        }),
        ('Generation', {
            'fields': ('generated_file', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'route',
                    'is_home', 'order', 'created_at']
    list_filter = ['is_home', 'created_at']
    search_fields = ['name', 'route']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'project', 'name', 'route', 'is_home', 'order')
        }),
        ('Screen Data', {
            'fields': ('json_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'created_by', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'type', 'description', 'thumbnail')
        }),
        ('Template', {
            'fields': ('template_json',),
            'classes': ('collapse',)
        }),
        ('Visibility', {
            'fields': ('created_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(GenerationLog)
class GenerationLogAdmin(admin.ModelAdmin):
    list_display = ['project', 'step', 'status', 'timestamp']
    list_filter = ['status', 'step', 'timestamp']
    search_fields = ['project__name', 'message']
    readonly_fields = ['timestamp']

    def has_add_permission(self, request):
        return False
