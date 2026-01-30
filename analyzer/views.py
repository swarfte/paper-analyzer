from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
import logging

from .services import analyze_paper

logger = logging.getLogger(__name__)


@login_required(login_url='/login/')
def analyzer(request):
    """
    Paper analyzer page view - requires authentication.
    """
    return render(request, 'analyzer.html')


@login_required(login_url='/login/')
@require_POST
def analyze_pdf(request):
    """
    Handle PDF analysis request.
    """
    if 'pdf_file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No PDF file uploaded. Please select a file.'
        }, status=400)

    pdf_file = request.FILES['pdf_file']

    # Validate file type
    if not pdf_file.name.endswith('.pdf'):
        return JsonResponse({
            'success': False,
            'error': 'Invalid file format. Please upload a PDF file.'
        }, status=400)

    # Validate file size (10MB max)
    if pdf_file.size > 10 * 1024 * 1024:
        return JsonResponse({
            'success': False,
            'error': 'File size exceeds 10MB limit.'
        }, status=400)

    try:
        # Analyze the paper
        analysis_result = analyze_paper(pdf_file)

        return JsonResponse({
            'success': True,
            'analysis': analysis_result
        })

    except Exception as e:
        logger.error(f"Paper analysis error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url='/login/')
def generator(request):
    """
    PPT generator page view - requires authentication.
    """
    return render(request, 'generator.html')


@csrf_protect
@require_http_methods(["GET", "POST"])
def custom_login(request):
    """
    Custom login view that handles both regular form submissions and AJAX requests.
    """
    if request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect': '/analyzer/'})
        return redirect('/analyzer/')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            # AuthenticationForm already authenticates the user in is_valid()
            # Get the user from the form
            user = form.get_user()

            if user is not None:
                login(request, user)

                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect': request.GET.get('next', '/analyzer/')
                    })

                # Regular form submission - redirect to next page or analyzer
                next_page = request.GET.get('next', '/analyzer/')
                return redirect(next_page)
            else:
                # This shouldn't happen if form.is_valid() is True, but just in case
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Authentication failed. Please try again.'
                    }, status=400)
        else:
            # Form validation errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, errors_list in form.errors.items():
                    errors[field] = ' '.join([str(e) for e in errors_list])

                # Get the first error message to display
                error_message = 'Please correct the errors below.'
                if '__all__' in errors:
                    error_message = errors['__all__']
                elif 'username' in errors:
                    error_message = errors['username']
                elif 'password' in errors:
                    error_message = errors['password']

                return JsonResponse({
                    'success': False,
                    'error': error_message,
                    'errors': errors
                }, status=400)

    # GET request - render the login form
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def custom_logout(request):
    """
    Custom logout view.
    """
    logout(request)
    return redirect('/login/')

