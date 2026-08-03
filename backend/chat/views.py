from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from repos.models import Repository
from .models import ChatMessage, ChatSession
from .serializers import ChatMessageSerializer, ChatSessionSerializer, SendMessageSerializer
from .services.rag import answer_question


def _get_repo_or_404(user, repo_id):
    try:
        return Repository.objects.get(id=repo_id, user=user)
    except Repository.DoesNotExist:
        return None


class ChatMessageView(APIView):
    def post(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if repository is None:
            return Response({'error': 'Repository not found'}, status=status.HTTP_404_NOT_FOUND)
        if repository.status == 'failed':
            return Response(
                {'error': f'Repository indexing failed, so chat is unavailable: {repository.error_message}'},
                status=status.HTTP_409_CONFLICT,
            )
        if repository.status != 'completed':
            return Response(
                {'error': f'Repository indexing is still in progress (status: {repository.status})'},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['message']
        session_id = serializer.validated_data['session_id']

        session, _ = ChatSession.objects.get_or_create(repository=repository, session_id=session_id)
        history = list(session.messages.all())
        history_payload = [{'role': m.role, 'content': m.content} for m in history]

        ChatMessage.objects.create(session=session, role='user', content=question)

        try:
            answer, citations = answer_question(repository, question, history_payload)
        except Exception as exc:  # noqa: BLE001
            return Response({'error': f'Failed to generate an answer: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

        ChatMessage.objects.create(session=session, role='assistant', content=answer, citations=citations)
        session.save(update_fields=['updated_at'])

        return Response({'answer': answer, 'citations': citations})


class ChatHistoryView(APIView):
    def get(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if repository is None:
            return Response({'error': 'Repository not found'}, status=status.HTTP_404_NOT_FOUND)

        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'messages': []})

        session = ChatSession.objects.filter(repository=repository, session_id=session_id).first()
        if not session:
            return Response({'messages': []})

        messages = ChatMessageSerializer(session.messages.all(), many=True).data
        return Response({'messages': messages})


class ChatSessionListView(APIView):
    def get(self, request, repo_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if repository is None:
            return Response({'error': 'Repository not found'}, status=status.HTTP_404_NOT_FOUND)

        sessions = repository.chat_sessions.all()
        return Response({'sessions': ChatSessionSerializer(sessions, many=True).data})


class ChatSessionDetailView(APIView):
    def delete(self, request, repo_id, session_id):
        repository = _get_repo_or_404(request.user, repo_id)
        if repository is None:
            return Response({'error': 'Repository not found'}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = ChatSession.objects.filter(repository=repository, session_id=session_id).delete()
        if not deleted:
            return Response({'error': 'Chat session not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
