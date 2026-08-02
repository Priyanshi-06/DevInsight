from rest_framework import serializers
from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['role', 'content', 'citations', 'created_at']


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    session_id = serializers.CharField()
