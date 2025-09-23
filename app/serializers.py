from rest_framework import serializers
from .models import Profile, Chat, Message, Te_status
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = '__all__'

class ChatSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Chat
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    # تم تبسيط حقل "chat" ليستخدم PrimaryKeyRelatedField بشكل مباشر.
    chat_id = serializers.PrimaryKeyRelatedField(
        queryset=Chat.objects.all(),
        source="chat",
    )
    
    class Meta:
        model = Message
        fields = '__all__'

class TeStatusSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Te_status
        fields = '__all__'