from rest_framework import serializers
from .models import Repository


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = [
            'id', 'github_url', 'owner', 'name', 'display_name', 'default_branch',
            'description', 'language', 'stars', 'status', 'error_message',
            'file_tree', 'chunk_count', 'created_at', 'updated_at',
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


class UpdateRepositorySerializer(serializers.Serializer):
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
