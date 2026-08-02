from rest_framework import serializers
from .models import ArchitectureSnapshot, Recommendation, PrDraft


class ArchitectureSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchitectureSnapshot
        fields = [
            'hld_mermaid', 'hld_group_diagrams', 'lld_diagrams', 'lld_descriptions',
            'summary', 'module_stats', 'generated_at',
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = [
            'id', 'issue_number', 'title', 'url', 'labels', 'beginner_labeled',
            'body_snippet', 'ai_summary', 'suggested_files', 'created_at',
        ]


class PrDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrDraft
        fields = [
            'id', 'issue_number', 'task_description', 'target_file', 'branch_name',
            'pr_title', 'explanation', 'diff_text', 'created_at',
        ]


class CreatePrDraftSerializer(serializers.Serializer):
    issue_number = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    task_description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data.get('issue_number') and not data.get('task_description'):
            raise serializers.ValidationError('Provide either issue_number or task_description.')
        return data
