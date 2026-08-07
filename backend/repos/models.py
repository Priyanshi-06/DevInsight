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
    # Purely cosmetic — a personal label shown instead of "owner/name" in the UI. Never used for
    # GitHub API calls (those always use owner/name, the real identifiers), so it's safe to let
    # the user set this to anything without touching ingestion, re-indexing, or file fetching.
    display_name = models.CharField(max_length=255, blank=True, default='')
    default_branch = models.CharField(max_length=255, default='main')
    description = models.TextField(blank=True, default='')
    language = models.CharField(max_length=100, blank=True, default='')
    stars = models.IntegerField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, default='')
    file_tree = models.JSONField(default=list, blank=True)
    chunk_count = models.IntegerField(default=0)
    # The commit SHA that was actually indexed, captured at ingestion time — compared against the
    # branch's current HEAD to detect when the indexed snapshot has gone stale.
    last_indexed_commit_sha = models.CharField(max_length=40, blank=True, default='')
    # Top-level folders (e.g. ['src', 'backend']) chosen for a large repo instead of indexing
    # everything — empty list means "index the whole repo" (the default, unchanged behavior for
    # any repo under the size/file-count threshold). Persisted so a later re-index reuses the
    # same scope automatically.
    scoped_paths = models.JSONField(default=list, blank=True)

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
