from django.contrib import admin
from .models import Profile, Chat, Message, Te_status
# Register your models here.


admin.site.register(Profile)
admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(Te_status)