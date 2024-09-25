# middleware.py
from django.shortcuts import redirect
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that do not require login
        exempt_paths = [
            settings.LOGIN_URL,
            '/accounts/signup/',
            '/accounts/google/login/',
            '/accounts/google/login/callback/'
        ]

        # If the user is not authenticated and the path is not exempt
        if not request.user.is_authenticated and request.path not in exempt_paths:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')

        response = self.get_response(request)
        return response
