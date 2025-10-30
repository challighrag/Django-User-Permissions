from django.contrib import admin
from .models import User, Task, Token

admin.site.register(User)
admin.site.register(Task)
admin.site.register(Token)