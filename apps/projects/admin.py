from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "path", "description", "last_synced")
    search_fields = ("name", "path", "description")
    readonly_fields = ("created_at", "last_synced")
