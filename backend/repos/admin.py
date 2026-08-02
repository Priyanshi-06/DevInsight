from django.contrib import admin
from .models import Repository, IngestionJob


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name', 'status', 'chunk_count', 'created_at')
    list_filter = ('status',)
    search_fields = ('owner', 'name')


admin.site.register(IngestionJob)
