from django.conf import settings
from django.db import models


class Repository(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('fetching', 'Fetching'),
        ('chunking', 'Chunking'),
        ('embedding', 'Embedding'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='repositories')
    github_url = models.URLField()
    owner = models.CharField(max_length=255)  # the GitHub repo's owner/org, e.g. "pallets" — not the app user
    name = models.CharField(max_length=255)
    default_branch = models.CharField(max_length=255, default='main')
    description = models.TextField(blank=True, default='')
    language = models.CharField(max_length=100, blank=True, default='')
    stars = models.IntegerField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, default='')
    file_tree = models.JSONField(default=list, blank=True)
    chunk_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'owner', 'name')

    def __str__(self):
        return f'{self.owner}/{self.name}'


class IngestionJob(models.Model):
    repository = models.OneToOneField(Repository, on_delete=models.CASCADE, related_name='ingestion_job')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    log = models.TextField(blank=True, default='')

    def __str__(self):
        return f'IngestionJob({self.repository})'
