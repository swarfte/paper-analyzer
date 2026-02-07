from django.shortcuts import redirect
from django.urls import resolve


class RedirectToAnalyzerMiddleware:
    """
    Middleware to redirect non-existent pages to the analyzer page.
    This works regardless of DEBUG mode.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # If response is 404, redirect to analyzer
        if response.status_code == 404:
            return redirect('/analyzer/')

        return response
