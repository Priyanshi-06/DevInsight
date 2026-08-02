import threading

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import IngestionJob, Repository
from .serializers import (
    CreateRepositorySerializer,
    RepositoryListSerializer,
    RepositorySerializer,
)
from .services import fetch
from .services.ingest import run_ingestion
from .services.fetch import RepoFetchError
from vectorstore.client import delete_collection


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
        IngestionJob.objects.create(repository=repository)

        thread = threading.Thread(target=run_ingestion, args=(repository,), daemon=True)
        thread.start()

        return Response(RepositorySerializer(repository).data, status=status.HTTP_202_ACCEPTED)


class RepositoryDetailView(APIView):
    def get(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if isinstance(repository, Response):
            return repository
        return Response(RepositorySerializer(repository).data)

    def delete(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if isinstance(repository, Response):
            return repository
        delete_collection(repository.id)
        repository.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _get_repo_or_404(user, repo_id):
    try:
        return Repository.objects.get(id=repo_id, user=user)
    except Repository.DoesNotExist:
        return Response({'error': 'Repository not found'}, status=status.HTTP_404_NOT_FOUND)
