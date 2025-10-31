import secrets
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from rest_framework import viewsets
from .authentication import TokenAuthentication
from .permissions import TokenPermissions
from rest_framework.authentication import BasicAuthentication
from .models import User, Task, Token
from .serializers import UserSerializer, TaskSerializer


# === User API ViewSet ===
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class TaskViewSet(viewsets.ModelViewSet):
    authentication_classes = [BasicAuthentication,TokenAuthentication]
    permission_classes = [TokenPermissions]
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

# === Guest Page ===
def guest(request):
    return render(request, 'guest.html')


# === User Registration & Login ===
def login_view(request):
    message = ''

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- REGISTER ---
        if action == 'register':
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')

            if email and password and first_name:
                if User.objects.filter(email=email).exists():
                    message = "Email already registered."
                else:
                    user = User.objects.create_user(email=email, password=password, first_name=first_name)
                    # create token for user
                    token_key = secrets.token_hex(20)
                    Token.objects.create(user=user, key=token_key)
                    request.session['token'] = token_key
                    login(request, user)
                    return redirect('home')
            else:
                message = "Email and password are required."

        # --- LOGIN ---
        elif action == 'login':
            email = request.POST.get('email')
            password = request.POST.get('password')

            user = authenticate(request, email=email, password=password)
            if user is not None:
                try:
                    token = Token.objects.get(user=user)
                except Token.DoesNotExist:
                    token = Token.objects.create(user=user, key=secrets.token_hex(20))

                request.session['token'] = token.key
                print("Session Token Set: ", request.session.items())
                login(request, user)
                return redirect('home')
            else:
                message = "Invalid email or password."

    return render(request, 'login.html', {'message': message})


# === Logout ===
def logout_view(request):
    logout(request)
    try:
        del request.session['token']
    except KeyError:
        pass
    return redirect('guest')


# === Home Page ===
def home(request):
    session_token = request.session.get('token')
    if not session_token:
        return redirect('guest')

    try:
        token_obj = Token.objects.get(key=session_token)
        user = token_obj.user
    except Token.DoesNotExist:
        return redirect('guest')

    message = ''
    user_found = None

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- Add Task ---
        if action == 'add_task':
            task_title = request.POST.get('task_name')
            description = request.POST.get('description')

            if task_title:
                Task.objects.create(
                    user=user,
                    title=task_title,
                    description=description
                )
                message = "Task added successfully!"
            else:
                message = "Task title required."

        # --- Logout ---
        elif action == 'logout':
            return logout_view(request)
    
    query = request.GET.get('search', '') 
    if query: 
        user_found = User.objects.filter(first_name__icontains=query) | User.objects.filter(email__icontains=query)

    tasks = Task.objects.all()
    print(tasks)
    return render(request, 'index.html', {
        'message': message,
        'user_found': user_found, #if query else None,
        'query': query,
        'user': user,
        'tasks': tasks,
        'token': session_token
    })


# === Delete User (with permission check) ===
def delete_user(request, user_id):
    session_token = request.session.get('token')
    if not session_token:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        token_obj = Token.objects.get(key=session_token)
        if not token_obj.permissions.filter(codename='delete_user').exists():
            return JsonResponse({'error': 'Permission denied'}, status=403)

        user_to_delete = User.objects.get(id=user_id)
        user_to_delete.delete()
        return JsonResponse({'message': 'User deleted successfully'})
    except Token.DoesNotExist:
        return JsonResponse({'error': 'Invalid token'}, status=401)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


# === Example Action with Permission ===
def api_action(request, perm_codename):
    session_token = request.session.get('token')
    if not session_token:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        token_obj = Token.objects.get(key=session_token)
        if not token_obj.permissions.filter(codename=perm_codename).exists():
            return JsonResponse({'error': 'Permission denied'}, status=403)

        return JsonResponse({'message': f'Action {perm_codename} executed'}, status=200)
    except Token.DoesNotExist:
        return JsonResponse({'error': 'Invalid token'}, status=401)