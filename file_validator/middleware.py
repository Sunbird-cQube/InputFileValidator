from django.shortcuts import redirect
from django.urls import reverse


class StaffRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.user.is_authenticated
            and request.user.is_staff
            and not request.user.is_superuser  # Exclude admin users
            and not request.path.startswith(reverse('dashboard'))
        ):
            return redirect(reverse('dashboard'))

        return response
