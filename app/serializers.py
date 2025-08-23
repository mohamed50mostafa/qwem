from rest_framework import serializers
from .models import Profile, Chat, Message, Te_status
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) 
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
        write_only=True
    )

    class Meta:
        model = Profile
        fields = '__all__'

class ChatSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
        write_only=True
    )

    class Meta:
        model = Chat
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
        write_only=True,
        allow_null=True,
        required=False
    )
    chat = ChatSerializer(read_only=True)
    chat_id = serializers.PrimaryKeyRelatedField(
        queryset=Chat.objects.all(),
        source="chat",
        write_only=True
    )

    class Meta:
        model = Message
        fields = '__all__'

class TeStatusSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
        write_only=True
    )

    class Meta:
        model = Te_status
        fields = '__all__'