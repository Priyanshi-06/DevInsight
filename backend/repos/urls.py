from django.urls import path

from . import views
from chat.views import ChatHistoryView, ChatMessageView, ChatSessionDetailView, ChatSessionListView
from contrib.views import ArchitectureView, PrDraftView, RecommendationsView, TestSuiteView

urlpatterns = [
    path('repos/', views.RepositoryListCreateView.as_view(), name='repo-list-create'),
    path('repos/<int:repo_id>/', views.RepositoryDetailView.as_view(), name='repo-detail'),
    path('repos/<int:repo_id>/file/', views.RepositoryFileView.as_view(), name='repo-file'),
    path('repos/<int:repo_id>/staleness/', views.RepositoryStalenessView.as_view(), name='repo-staleness'),
    path('repos/<int:repo_id>/reindex/', views.RepositoryReindexView.as_view(), name='repo-reindex'),
    path('repos/<int:repo_id>/chat/', ChatMessageView.as_view(), name='repo-chat'),
    path('repos/<int:repo_id>/chat/history/', ChatHistoryView.as_view(), name='repo-chat-history'),
    path('repos/<int:repo_id>/chat/sessions/', ChatSessionListView.as_view(), name='repo-chat-sessions'),
    path(
        'repos/<int:repo_id>/chat/sessions/<str:session_id>/',
        ChatSessionDetailView.as_view(),
        name='repo-chat-session-detail',
    ),
    path('repos/<int:repo_id>/recommendations/', RecommendationsView.as_view(), name='repo-recommendations'),
    path('repos/<int:repo_id>/architecture/', ArchitectureView.as_view(), name='repo-architecture'),
    path('repos/<int:repo_id>/pr-draft/', PrDraftView.as_view(), name='repo-pr-draft'),
    path('repos/<int:repo_id>/tests/', TestSuiteView.as_view(), name='repo-test-suite'),
]
