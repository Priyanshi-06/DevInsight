from rest_framework import serializers
from .models import Repository


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = [
            'id', 'github_url', 'owner', 'name', 'display_name', 'default_branch',
            'description', 'language', 'stars', 'status', 'error_message',
            'file_tree', 'chunk_count', 'scoped_paths', 'created_at', 'updated_at',
        ]
        read_only_fields = [f for f in fields if f not in ('display_name', 'description')]


class RepositoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = [
            'id', 'github_url', 'owner', 'name', 'display_name', 'description',
            'language', 'stars', 'status', 'created_at',
        ]
        read_only_fields = fields


class CreateRepositorySerializer(serializers.Serializer):
    github_url = serializers.URLField()
    # Only meaningful on the resubmission after a "needs_folder_selection" response — omitted
    # (or empty) means "index the whole repo," same as before this feature existed.
    scoped_paths = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class UpdateRepositorySerializer(serializers.Serializer):
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
