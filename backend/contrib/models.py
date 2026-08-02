from django.db import models
from repos.models import Repository


class ArchitectureSnapshot(models.Model):
    repository = models.OneToOneField(Repository, on_delete=models.CASCADE, related_name='architecture')
    hld_mermaid = models.TextField(blank=True, default='')
    hld_group_diagrams = models.JSONField(default=list, blank=True)
    lld_diagrams = models.JSONField(default=list, blank=True)
    lld_descriptions = models.JSONField(default=list, blank=True)
    summary = models.TextField(blank=True, default='')
    module_stats = models.JSONField(default=list, blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Architecture({self.repository})'


class Recommendation(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='recommendations')
    issue_number = models.IntegerField()
    title = models.CharField(max_length=500)
    url = models.URLField()
    labels = models.JSONField(default=list, blank=True)
    beginner_labeled = models.BooleanField(default=False)
    body_snippet = models.TextField(blank=True, default='')
    ai_summary = models.TextField(blank=True, default='')
    suggested_files = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-beginner_labeled', 'id']
        unique_together = ('repository', 'issue_number')

    def __str__(self):
        return f'#{self.issue_number} {self.title}'


class PrDraft(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='pr_drafts')
    issue_number = models.IntegerField(null=True, blank=True)
    task_description = models.TextField()
    target_file = models.CharField(max_length=1000)
    branch_name = models.CharField(max_length=255, blank=True, default='')
    pr_title = models.CharField(max_length=500, blank=True, default='')
    explanation = models.TextField(blank=True, default='')
    diff_text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'PrDraft({self.repository}, {self.target_file})'
