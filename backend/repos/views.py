import threading

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import IngestionJob, Repository
from .serializers import (
    CreateRepositorySerializer,
    RepositoryListSerializer,
    RepositorySerializer,
    UpdateRepositorySerializer,
)
from .services import fetch
from .services.ingest import run_ingestion
from .services.fetch import RepoFetchError
from vectorstore.client import delete_collection

# Large enough for virtually any source file, small enough to avoid dumping huge
# minified/generated files into the browser.
MAX_FILE_PREVIEW_BYTES = 300_000

IN_PROGRESS_STATUSES = ('pending', 'fetching', 'chunking', 'embedding')


def _start_ingestion(repository):
    IngestionJob.objects.filter(repository=repository).delete()
    IngestionJob.objects.create(repository=repository)
    repository.status = 'pending'
    repository.save(update_fields=['status', 'updated_at'])

    thread = threading.Thread(target=run_ingestion, args=(repository,), daemon=True)
    thread.start()


class RepositoryListCreateView(APIView):
    def get(self, request):
        repos = Repository.objects.filter(user=request.user)
        return Response(RepositoryListSerializer(repos, many=True).data)

    def post(self, request):
        serializer = CreateRepositorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        github_url = serializer.validated_data['github_url']

        try:
            owner, name = fetch.parse_github_url(github_url)
        except RepoFetchError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        existing = Repository.objects.filter(user=request.user, owner__iexact=owner, name__iexact=name).first()
        if existing:
            return Response(RepositorySerializer(existing).data, status=status.HTTP_200_OK)

        repository = Repository.objects.create(
            user=request.user, github_url=github_url, owner=owner, name=name, status='pending',
        )
        _start_ingestion(repository)

        return Response(RepositorySerializer(repository).data, status=status.HTTP_202_ACCEPTED)


class RepositoryDetailView(APIView):
    def get(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if isinstance(repository, Response):
            return repository
        return Response(RepositorySerializer(repository).data)

    def patch(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if isinstance(repository, Response):
            return repository

        serializer = UpdateRepositorySerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        update_fields = []
        if 'display_name' in serializer.validated_data:
            repository.display_name = serializer.validated_data['display_name'].strip()
            update_fields.append('display_name')
        if 'description' in serializer.validated_data:
            repository.description = serializer.validated_data['description'].strip()
            update_fields.append('description')

        if update_fields:
            repository.save(update_fields=[*update_fields, 'updated_at'])

        return Response(RepositorySerializer(repository).data)

    def delete(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if isinstance(repository, Response):
            return repository
        delete_collection(repository.id)
        repository.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RepositoryFileView(APIView):
    """Serves the content of one indexed file, fetched fresh from GitHub's raw content endpoint
    (lightweight, one file at a time — unlike the full tarball download used for ingestion/PR
    drafts). Powers the code viewer: clicking a chat citation or a file-tree entry."""

    def get(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if isinstance(repository, Response):
            return repository

        path = request.query_params.get('path')
        if not path:
            return Response({'error': 'path query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        if path not in (repository.file_tree or []):
            return Response(
                {'error': "That file isn't in this repository's indexed file tree."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            content, truncated = fetch.fetch_raw_file(
                repository.owner, repository.name, repository.default_branch, path,
                max_bytes=MAX_FILE_PREVIEW_BYTES,
            )
        except RepoFetchError as exc:
            status_code = (
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE if 'binary' in str(exc) else status.HTTP_502_BAD_GATEWAY
            )
            return Response({'error': str(exc)}, status=status_code)

        return Response({'path': path, 'content': content, 'truncated': truncated})


class RepositoryStalenessView(APIView):
    """Checks whether the source repo's default branch has moved past the commit that was
    actually indexed. A separate, on-demand endpoint (rather than folding this into the repo
    detail response) so it's never fired on every poll — just once when a completed repo's
    dashboard loads — to stay well within GitHub's unauthenticated rate limit."""

    def get(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if isinstance(repository, Response):
            return repository

        if repository.status != 'completed':
            return Response({'is_stale': False, 'indexed_commit': repository.last_indexed_commit_sha or None, 'latest_commit': None})

        try:
            latest_sha = fetch.fetch_latest_commit_sha(
                repository.owner, repository.name, repository.default_branch,
            )
        except RepoFetchError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        is_stale = bool(repository.last_indexed_commit_sha) and latest_sha != repository.last_indexed_commit_sha
        return Response({
            'is_stale': is_stale,
            'indexed_commit': repository.last_indexed_commit_sha or None,
            'latest_commit': latest_sha,
        })


class RepositoryReindexView(APIView):
    def post(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if isinstance(repository, Response):
            return repository

        if repository.status in IN_PROGRESS_STATUSES:
            return Response({'error': 'Indexing is already in progress.'}, status=status.HTTP_409_CONFLICT)

        _start_ingestion(repository)
        return Response(RepositorySerializer(repository).data, status=status.HTTP_202_ACCEPTED)


def _get_repo_or_404(user, repo_id):
    try:
        return Repository.objects.get(id=repo_id, user=user)
    except Repository.DoesNotExist:
        return Response({'error': 'Repository not found'}, status=status.HTTP_404_NOT_FOUND)
