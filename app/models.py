from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    GENDER_CHOICES = [('male', 'male'), ('female', 'female')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_parent = models.BooleanField(default=False)
    sons = models.ManyToManyField(User, related_name='parent_profiles', blank=True)

    image = models.ImageField(default='default.jpg', upload_to='profile_pics', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True, null=True, default="")
    age = models.PositiveIntegerField(null=True, blank=True, default=None)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, null=True, blank=True, default=None)
    job = models.CharField(max_length=100, blank=True, null=True, default="")

    def __str__(self):
        return f'{self.user.username} Profile'


class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    chat_name = models.CharField(max_length=100, default="New Chat")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.chat_name


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) 
    ai = models.BooleanField(default=False)
    image = models.ImageField(upload_to='chat_images', null=True, blank=True)
    content = models.TextField(default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.ai:
            return f'AI: {self.content[:30]}...'
        elif self.user:
            return f'{self.user.username}: {self.content[:30]}...'
        return f'Unknown: {self.content[:30]}...'


class Te_status(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='statuses')
    persona_prompt = models.TextField(max_length=500, null=True, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.username} Status'