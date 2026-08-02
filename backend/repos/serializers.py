from rest_framework import serializers
from .models import Repository


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = [
            'id', 'github_url', 'owner', 'name', 'default_branch',
            'description', 'language', 'stars', 'status', 'error_message',
            'file_tree', 'chunk_count', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class RepositoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = [
            'id', 'github_url', 'owner', 'name', 'description',
            'language', 'stars', 'status', 'created_at',
        ]
        read_only_fields = fields


class CreateRepositorySerializer(serializers.Serializer):
    github_url = serializers.URLField()
