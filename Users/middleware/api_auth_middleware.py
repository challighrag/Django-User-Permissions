from django.http import JsonResponse
from ..models import Token

class apiAuth:
    def __init__(self, get_response):
         self.get_response = get_response

    def __call__(self, request):
    #     # Skip authentication for these paths
    #     if request.path.startswith('/'):# or request.path.startswith('/login/'):
    #         return self.get_response(request)

    #     token_header = request.session.get('token')
    #     if not token_header:
    #         return JsonResponse({'error': 'Missing API token'}, status=401)

    #     try:
    #         stored_token = Token.objects.filter(key=token_header).first()
    #         if not stored_token or token_header.strip() != stored_token.key:
    #             return JsonResponse({'error': 'Invalid or unauthorized token'}, status=403)

    #         request.user = stored_token.user
    #         request.token_permissions = stored_token.permissions.all()

    #     except Exception as e:
    #         print("Middleware error:", e)
    #         return JsonResponse({'error': 'Server error'}, status=500)

        return self.get_response(request)