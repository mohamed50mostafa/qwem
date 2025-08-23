from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet, ChatViewSet, MessageViewSet, TeStatusViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet)
router.register(r'chats', ChatViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'te_statuses', TeStatusViewSet)

urlpatterns = [
    path('', include(router.urls)),
]