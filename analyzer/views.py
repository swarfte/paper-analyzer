from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import models
from django.conf import settings
import json
import logging
import os
from datetime import datetime

from .services import analyze_paper
from .models import PaperAnalysis

logger = logging.getLogger(__name__)


@login_required(login_url='/login/')
def analyzer(request):
    """
    Paper analyzer page view - requires authentication.
    """
    context = {
        'max_pdf_size_mb': settings.MAX_PDF_SIZE_MB,
    }
    return render(request, 'analyzer.html', context)


@login_required(login_url='/login/')
@require_POST
def analyze_pdf(request):
    """
    Handle PDF analysis request and save results to database.
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

    # Validate file size using settings
    max_size_bytes = settings.MAX_PDF_SIZE_MB * 1024 * 1024
    if pdf_file.size > max_size_bytes:
        return JsonResponse({
            'success': False,
            'error': f'File size exceeds {settings.MAX_PDF_SIZE_MB}MB limit.'
        }, status=400)

    try:
        # Analyze the paper
        analysis_result = analyze_paper(pdf_file)

        # Save to database
        paper_analysis = PaperAnalysis.objects.create(
            user=request.user,
            title=pdf_file.name.replace('.pdf', ''),
            pdf_file=pdf_file,
            original_filename=pdf_file.name,
            abstract=analysis_result.get('abstract', ''),
            motivation=analysis_result.get('motivation', ''),
            contribution=analysis_result.get('contribution', ''),
            what_does_paper_do=analysis_result.get('what_does_paper_do', ''),
            how_does_paper_do=analysis_result.get('how_does_paper_do', ''),
            limitations_challenges=analysis_result.get('limitations_challenges', ''),
            future_work=analysis_result.get('future_work', ''),
            conclusion=analysis_result.get('conclusion', ''),
            analysis_data=analysis_result
        )

        return JsonResponse({
            'success': True,
            'analysis': analysis_result,
            'analysis_id': paper_analysis.id
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


@login_required(login_url='/login/')
def analysis_history(request):
    """
    Display user's paper analysis history.
    """
    analyses = PaperAnalysis.objects.filter(user=request.user)

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        analyses = analyses.filter(
            models.Q(title__icontains=search_query) |
            models.Q(original_filename__icontains=search_query) |
            models.Q(abstract__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(analyses, 12)  # 12 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_count': analyses.count()
    }

    return render(request, 'analysis_history.html', context)


@login_required(login_url='/login/')
def analysis_detail(request, analysis_id):
    """
    View a specific paper analysis.
    """
    analysis = get_object_or_404(PaperAnalysis, id=analysis_id, user=request.user)

    # Build analysis result dict from model fields
    analysis_result = {
        'abstract': analysis.abstract,
        'motivation': analysis.motivation,
        'contribution': analysis.contribution,
        'what_does_paper_do': analysis.what_does_paper_do,
        'how_does_paper_do': analysis.how_does_paper_do,
        'limitations_challenges': analysis.limitations_challenges,
        'future_work': analysis.future_work,
        'conclusion': analysis.conclusion,
    }

    context = {
        'analysis': analysis,
        'analysis_result': analysis_result,
    }

    return render(request, 'analysis_detail.html', context)


@login_required(login_url='/login/')
@require_POST
def delete_analysis(request, analysis_id):
    """
    Delete a paper analysis.
    """
    analysis = get_object_or_404(PaperAnalysis, id=analysis_id, user=request.user)

    try:
        # Delete the PDF file
        if analysis.pdf_file and os.path.exists(analysis.pdf_file.path):
            os.remove(analysis.pdf_file.path)

        # Delete the database record
        analysis.delete()

        return JsonResponse({
            'success': True,
            'message': 'Analysis deleted successfully.'
        })

    except Exception as e:
        logger.error(f"Error deleting analysis: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url='/login/')
def analysis_list_api(request):
    """
    API endpoint to get user's analysis history (for AJAX requests).
    """
    analyses = PaperAnalysis.objects.filter(user=request.user).order_by('-created_date')

    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))

    paginator = Paginator(analyses, per_page)
    page_obj = paginator.get_page(page)

    data = {
        'analyses': [
            {
                'id': a.id,
                'title': a.title or a.original_filename,
                'original_filename': a.original_filename,
                'created_date': a.created_date.isoformat(),
                'file_size_mb': a.file_size_mb,
                'pdf_url': a.pdf_file.url if a.pdf_file else None,
                'abstract': a.abstract[:200] + '...' if a.abstract and len(a.abstract) > 200 else a.abstract,
            }
            for a in page_obj
        ],
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'num_pages': page_obj.paginator.num_pages,
        'current_page': page,
        'total_count': paginator.count,
    }

    return JsonResponse(data)


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

