# app/views.py

from rest_framework import viewsets
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q
import os

# --------------------------------------------------------------------------------
# NEW IMPORTS FOR THE HUGGING FACE TRANSFORMERS LIBRARY
# --------------------------------------------------------------------------------
from transformers import pipeline
from .models import Profile, Chat, Message, Te_status
from .serializers import ProfileSerializer, ChatSerializer, MessageSerializer, TeStatusSerializer


# --------------------------------------------------------------------------------
# LOAD THE TRANSFORMERS PIPELINE (Loaded once on server startup)
# --------------------------------------------------------------------------------
try:
    print("🔄 Attempting to load text-generation pipeline...")
    generation_pipe = pipeline(
        "text-generation",
        model="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" 
    )
    print("✅ Pipeline loaded successfully!")
except Exception as e:
    print(f"❌ Failed to load pipeline: {e}")
    generation_pipe = None


# --------------------------------------------------------------------------------
# VIEWS WITH THE NEW GENERATION LOGIC
# --------------------------------------------------------------------------------

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by("timestamp")
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        user_instance = serializer.validated_data['user']
        chat_instance = serializer.validated_data['chat']
        content = serializer.validated_data['content']

        # 1) Save user's message
        user_msg = serializer.save(user=user_instance, chat=chat_instance, content=content, ai=False)

        # 2) Generate AI reply using the new pipeline
        persona = self.get_or_create_persona(user_instance, content)
        full_prompt = self.create_ai_prompt(persona, content)
        ai_text = self.get_ai_response(full_prompt)

        # 3) Save AI's response
        ai_msg = Message.objects.create(chat=chat_instance, user=None, ai=True, content=ai_text)

        # 4) Return both messages
        return Response({
            "user_message": MessageSerializer(user_msg).data,
            "ai_message": MessageSerializer(ai_msg).data,
        }, status=201)

    def get_ai_response(self, full_prompt):
        """Generates AI response using the loaded Transformers pipeline."""
        if not generation_pipe:
            return "Pipeline is not loaded. Check server logs."
        
        try:
            output = generation_pipe(
                full_prompt,
                max_new_tokens=256,
                truncation=True,
                temperature=0.7,
                do_sample=True,
            )
            
            generated_text = output[0]['generated_text'].strip()
            ai_start_marker = "<|im_start|>assistant"
            if ai_start_marker in generated_text:
                return generated_text.split(ai_start_marker, 1)[1].strip()
            
            return generated_text
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return f"خطأ في توليد الرد من الذكاء الاصطناعي: {e}"

    def get_or_create_persona(self, user, content):
        """Retrieves user's persona or returns a default."""
        try:
            te_status = Te_status.objects.get(user=user)
            if te_status.persona_prompt:
                return te_status.persona_prompt
        except Te_status.DoesNotExist:
            pass
        return "شخصية ودودة ومرحة"

    def create_ai_prompt(self, persona, user_message):
        """
        Creates the full system-level prompt using DeepSeek's chat template.
        """
        return f"""<|im_start|>system
انت مساعد افتراضي مصري. 🇪🇬 مهمتك هي مساعدة المستخدمين من خلال الرد عليهم بأسلوب ودود ومساعد.
استخدم اللغة المصرية العامية فقط.
تأكد أن ردك يكون بناءً على شخصية المستخدم: {persona}
اجعل ردك طبيعياً ومختصراً قدر الإمكان.
<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
"""

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    def perform_create(self, serializer):
        user = self.request.user
        profile, created = Profile.objects.get_or_create(user=user)
        serializer.save(user=profile)
        return Response(serializer.data, status=201)
    def perform_update(self, serializer):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        serializer.save(user=profile)
        return Response(serializer.data, status=200)
    def retrieve(self, request, *args, **kwargs):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    def perform_create(self, serializer):
        user = self.request.user
        chat = serializer.save(user=user)
        return Response(ChatSerializer(chat).data, status=201)
    def retrieve(self, request, *args, **kwargs):
        user = self.request.user
        chat = self.get_object()
        if chat.user != user:
            return Response({"detail": "You do not have permission to view this chat."}, status=403)
        
        serializer = self.get_serializer(chat)
        return Response(serializer.data)

class TeStatusViewSet(viewsets.ModelViewSet):
    queryset = Te_status.objects.all()
    serializer_class = TeStatusSerializer
    def perform_create(self, serializer):
        user = self.request.user
        te_status, created = Te_status.objects.get_or_create(user=user)
        serializer.save(user=te_status)
        return Response(serializer.data, status=201)
    def perform_update(self, serializer):
        user = self.request.user
        te_status = Te_status.objects.get(user=user)
        serializer.save(user=te_status)
        return Response(serializer.data, status=200)
    def retrieve(self, request, *args, **kwargs):
        user = self.request.user
        te_status = Te_status.objects.get(user=user)
        serializer = self.get_serializer(te_status)
        return Response(serializer.data)