from rest_framework import serializers
from .models import ChatMessage

TITLE_MAX_CHARS = 60


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['role', 'content', 'citations', 'created_at']


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    session_id = serializers.CharField()


class ChatSessionSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    title = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_title(self, obj):
        first_message = obj.messages.filter(role='user').order_by('created_at').first()
        if not first_message:
            return 'New chat'
        text = first_message.content.strip()
        return text if len(text) <= TITLE_MAX_CHARS else text[:TITLE_MAX_CHARS].rstrip() + '…'

    def get_message_count(self, obj):
        return obj.messages.count()
