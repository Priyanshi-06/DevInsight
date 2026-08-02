from django.urls import path

from . import views
from chat.views import ChatMessageView, ChatHistoryView
from contrib.views import ArchitectureView, RecommendationsView, PrDraftView

urlpatterns = [
    path('repos/', views.RepositoryListCreateView.as_view(), name='repo-list-create'),
    path('repos/<int:repo_id>/', views.RepositoryDetailView.as_view(), name='repo-detail'),
    path('repos/<int:repo_id>/chat/', ChatMessageView.as_view(), name='repo-chat'),
    path('repos/<int:repo_id>/chat/history/', ChatHistoryView.as_view(), name='repo-chat-history'),
    path('repos/<int:repo_id>/recommendations/', RecommendationsView.as_view(), name='repo-recommendations'),
    path('repos/<int:repo_id>/architecture/', ArchitectureView.as_view(), name='repo-architecture'),
    path('repos/<int:repo_id>/pr-draft/', PrDraftView.as_view(), name='repo-pr-draft'),
]
