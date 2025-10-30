from rest_framework import serializers
from .models import User, Task, Token

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['__ALL__']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'user', 'title', 'description']