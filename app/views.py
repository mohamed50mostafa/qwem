from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
import os
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
# --------------------------------------------------------------------------------
# NEW IMPORTS FOR THE GEMINI AI API
# --------------------------------------------------------------------------------
import google.generativeai as genai
from .models import Profile, Chat, Message, Te_status
from .serializers import (
    ProfileSerializer,
    ChatSerializer,
    MessageSerializer,
    TeStatusSerializer,
    UserSerializer,
)

# --------------------------------------------------------------------------------
# IMPROVED REGISTER VIEW
# --------------------------------------------------------------------------------
@api_view(["POST"])
def register(request):
    """
    Handles user registration and creates an authentication token.
    Checks for existing users by email.
    """
    if request.method == "POST":
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")

        # 1. Validate required fields
        if not all([username, password, email]):
            return Response(
                {"error": "Username, password, and email are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Check for existing email to prevent duplicates
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Create the user with a hashed password
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            # Create or retrieve authentication token
            token, created = Token.objects.get_or_create(user=user)
            serializer = UserSerializer(user)

            return Response(
                {
                    "message": "User registered successfully",
                    "user": serializer.data,
                    "token": token.key,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(
        {"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


# --------------------------------------------------------------------------------
# CONFIGURE GEMINI AI (from environment variable for security)
# --------------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini AI configured successfully!")
else:
    print("❌ GEMINI_API_KEY not found. Please set the environment variable.")
    gemini_model = None


# --------------------------------------------------------------------------------
# REFACTORED VIEWS WITH BETTER LOGIC AND SECURITY
# --------------------------------------------------------------------------------
class MessageViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing chat messages and handling AI responses.
    """
    queryset = Message.objects.all().order_by("timestamp")
    serializer_class = MessageSerializer

    def get_queryset(self):
        """
        Filters messages to only show those for the current user's chats.
        Handles unauthenticated users gracefully.
        """
        if self.request.user.is_authenticated:
            return self.queryset.filter(
                chat__user=self.request.user
            ).order_by("timestamp")
        return Message.objects.none()


    def create(self, request, *args, **kwargs):
        """
        Handles creating a user's message and generating an AI reply.
        Handles unauthenticated users gracefully.
        """
        if not self.request.user.is_authenticated:
            return Response({"error": "Authentication required to create a message."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Create a mutable copy of the request data
        request_data = request.data.copy()
        request_data['user'] = request.user.id

        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user_instance = self.request.user
        chat_instance = serializer.validated_data['chat']
        content = serializer.validated_data['content']

        # 1) Save the user's message
        user_msg = serializer.save(user=user_instance, chat=chat_instance, content=content, ai=False)

        # 2) Generate AI reply using the Gemini API
        persona = self.get_or_create_persona(user_instance, content)
        full_prompt = self.create_ai_prompt(persona, content)
        ai_text = self.get_ai_response(full_prompt)

        # 3) Save the AI's response to the database
        ai_msg = Message.objects.create(chat=chat_instance, user=None, ai=True, content=ai_text)
        
        # 4) Return both messages in a structured response
        return Response({
            "user_message": MessageSerializer(user_msg, context={'request': request}).data,
            "ai_message": MessageSerializer(ai_msg, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)

    def get_ai_response(self, full_prompt):
        """Generates AI response using the configured Gemini model."""
        if not gemini_model:
            return "Gemini AI is not configured. Check server logs."
        
        try:
            response = gemini_model.generate_content(full_prompt)
            # The generated content is in the 'text' attribute of the response
            return response.text.strip()
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
        Creates the full prompt for Gemini.
        """
        return f"""
        انت مساعد افتراضي مصري. 🇪🇬 مهمتك هي مساعدة المستخدمين من خلال الرد عليهم بأسلوب ودود ومساعد.
        استخدم اللغة المصرية العامية فقط.
        تأكد أن ردك يكون بناءً على شخصية المستخدم: {persona}
        اجعل ردك طبيعياً ومختصراً قدر الإمكان.
        {user_message}
        """

class ProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing user profiles.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        """
        Restricts queryset to the current user's profile.
        Handles unauthenticated users gracefully.
        """
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return Profile.objects.none()
    
    def perform_create(self, serializer):
        """Ensures a user can only create their own profile."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            return Response({"error": "Authentication required to create a profile."}, status=status.HTTP_401_UNAUTHORIZED)
    
    def perform_update(self, serializer):
        """Ensures a user can only update their own profile."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            return Response({"error": "Authentication required to update a profile."}, status=status.HTTP_401_UNAUTHORIZED)

class ChatViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing chat sessions.
    """
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def get_queryset(self):
        """
        Restricts queryset to chats belonging to the current user.
        Handles unauthenticated users gracefully.
        """
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return Chat.objects.none()

    def perform_create(self, serializer):
        """Ensures a user can only create a chat for themselves."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            return Response({"error": "Authentication required to create a chat."}, status=status.HTTP_401_UNAUTHORIZED)

class TeStatusViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing the user's Te_status, which includes the AI persona.
    """
    queryset = Te_status.objects.all()
    serializer_class = TeStatusSerializer

    def get_queryset(self):
        """
        Restricts queryset to the current user's Te_status.
        Handles unauthenticated users gracefully.
        """
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return Te_status.objects.none()

    def perform_create(self, serializer):
        """Ensures a user can only create their own Te_status."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            return Response({"error": "Authentication required to create a status."}, status=status.HTTP_401_UNAUTHORIZED)

    def perform_update(self, serializer):
        """Ensures a user can only update their own Te_status."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            return Response({"error": "Authentication required to update a status."}, status=status.HTTP_401_UNAUTHORIZED)