from django.db import models
from repos.models import Repository


class ChatSession(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Bumped on every new message so the session list can sort by recent activity, not just
    # creation order.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('repository', 'session_id')
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.repository} / {self.session_id}'


class ChatMessage(models.Model):
    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    citations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'
