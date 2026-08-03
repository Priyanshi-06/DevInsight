from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from repos.models import Repository

from .serializers import (
    ArchitectureSnapshotSerializer,
    CreatePrDraftSerializer,
    CreateTestSuiteSerializer,
    PrDraftSerializer,
    RecommendationSerializer,
    TestSuiteDraftSerializer,
)
from .services.architecture import generate_architecture
from .services.pr_draft import PrDraftError, generate_pr_draft
from .services.recommendations import generate_recommendations
from .services.test_generator import TestGeneratorError, generate_test_suite


def _get_repo_or_404(user, repo_id):
    try:
        return Repository.objects.get(id=repo_id, user=user)
    except Repository.DoesNotExist:
        return None


def _require_completed_repo(user, repo_id):
    repository = _get_repo_or_404(user, repo_id)
    if repository is None:
        return None, Response({'error': 'Repository not found'}, status=status.HTTP_404_NOT_FOUND)
    if repository.status == 'failed':
        return None, Response(
            {'error': f'Repository indexing failed, so this feature is unavailable: {repository.error_message}'},
            status=status.HTTP_409_CONFLICT,
        )
    if repository.status != 'completed':
        return None, Response(
            {'error': f'Repository indexing is still in progress (status: {repository.status})'},
            status=status.HTTP_409_CONFLICT,
        )
    return repository, None


class ArchitectureView(APIView):
    def get(self, request, repo_id):
        repository, error = _require_completed_repo(request.user, repo_id)
        if error:
            return error

        force = request.query_params.get('refresh') == 'true'
        try:
            snapshot, generated = generate_architecture(repository, force=force)
        except Exception as exc:  # noqa: BLE001
            return Response({'error': f'Failed to generate architecture diagram: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

        data = ArchitectureSnapshotSerializer(snapshot).data
        data['generated'] = generated
        return Response(data)


class RecommendationsView(APIView):
    def get(self, request, repo_id):
        repository, error = _require_completed_repo(request.user, repo_id)
        if error:
            return error

        force = request.query_params.get('refresh') == 'true'
        recommendations, generated, message = generate_recommendations(repository, force=force)

        return Response({
            'recommendations': RecommendationSerializer(recommendations, many=True).data,
            'generated': generated,
            'message': message,
        })


class PrDraftView(APIView):
    def get(self, request, repo_id):
        repository, error = _require_completed_repo(request.user, repo_id)
        if error:
            return error

        drafts = repository.pr_drafts.all()
        return Response({'drafts': PrDraftSerializer(drafts, many=True).data})

    def post(self, request, repo_id):
        repository, error = _require_completed_repo(request.user, repo_id)
        if error:
            return error

        serializer = CreatePrDraftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            draft = generate_pr_draft(
                repository,
                issue_number=serializer.validated_data.get('issue_number'),
                task_description=serializer.validated_data.get('task_description'),
            )
        except PrDraftError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            return Response({'error': f'Failed to generate PR draft: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(PrDraftSerializer(draft).data, status=status.HTTP_201_CREATED)


class TestSuiteView(APIView):
    def get(self, request, repo_id):
        repository, error = _require_completed_repo(request.user, repo_id)
        if error:
            return error

        drafts = repository.test_drafts.all()
        return Response({'drafts': TestSuiteDraftSerializer(drafts, many=True).data})

    def post(self, request, repo_id):
        repository, error = _require_completed_repo(request.user, repo_id)
        if error:
            return error

        serializer = CreateTestSuiteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            draft = generate_test_suite(
                repository,
                target_file=serializer.validated_data.get('target_file') or None,
                task_description=serializer.validated_data.get('task_description'),
            )
        except TestGeneratorError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            return Response({'error': f'Failed to generate tests: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(TestSuiteDraftSerializer(draft).data, status=status.HTTP_201_CREATED)
