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
from django.template.loader import render_to_string
import json
import logging
import os
from datetime import datetime
import markdown
import re
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

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


@login_required(login_url='/login/')
def export_analysis_pdf(request, analysis_id):
    """
    Export an analysis as a PDF file using ReportLab with proper markdown formatting.
    """
    analysis = get_object_or_404(PaperAnalysis, id=analysis_id, user=request.user)

    try:
        # Create filename
        safe_title = analysis.title.replace(' ', '_').replace('/', '_').replace('\\', '_')[:100]
        filename = f"{safe_title}_analysis_report.pdf"

        # Create HttpResponse with PDF content type
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Create PDF document
        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=HexColor('#1e3a8a'),
            spaceAfter=20,
            spaceBefore=20,
            alignment=TA_LEFT,
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=15,
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=16,
        )

        code_style = ParagraphStyle(
            'Code',
            parent=styles['Code'],
            fontSize=9,
            leftIndent=20,
            spaceAfter=12,
            spaceBefore=6,
            backColor=HexColor('#f3f4f6'),
        )

        def parse_markdown_to_flowables(text, body_style, code_style):
            """Parse markdown text and convert to ReportLab flowables."""
            if not text:
                return []

            flowables = []
            lines = text.split('\n')
            i = 0

            while i < len(lines):
                line = lines[i].strip()

                # Empty line - add spacer
                if not line:
                    i += 1
                    continue

                # Code block (``` or ~~~)
                if line.startswith('```') or line.startswith('~~~'):
                    i += 1
                    code_lines = []
                    while i < len(lines) and not lines[i].strip().startswith('```') and not lines[i].strip().startswith('~~~'):
                        code_lines.append(lines[i])
                        i += 1
                    code_text = '<br/>'.join(code_lines)
                    flowables.append(Paragraph(f'<code>{code_text}</code>', code_style))
                    i += 1
                    continue

                # Bullet list item
                if line.startswith('- ') or line.startswith('* '):
                    bullet_items = []
                    while i < len(lines):
                        curr_line = lines[i].strip()
                        if not curr_line.startswith('- ') and not curr_line.startswith('* '):
                            break
                        # Remove bullet marker and convert to HTML
                        item_text = curr_line[2:].strip()
                        item_text = markdown_to_html_inline(item_text)
                        bullet_items.append(ListItem(Paragraph(item_text, body_style)))
                        i += 1
                    if bullet_items:
                        flowables.append(ListFlowable(bullet_items, bulletType='bullet', leftIndent=20, spaceBefore=6, spaceAfter=6))
                    continue

                # Numbered list item
                numbered_match = re.match(r'^(\d+)\.\s+(.*)$', line)
                if numbered_match:
                    num = numbered_match.group(1)
                    item_text = numbered_match.group(2).strip()
                    item_text = markdown_to_html_inline(item_text)
                    flowables.append(Paragraph(f'{num}. {item_text}', body_style))
                    i += 1
                    continue

                # Header
                if line.startswith('###'):
                    header_text = line[3:].strip()
                    header_text = markdown_to_html_inline(header_text)
                    flowables.append(Paragraph(f'<b>{header_text}</b>', body_style))
                    flowables.append(Spacer(1, 0.1 * inch))
                    i += 1
                    continue
                elif line.startswith('##'):
                    header_text = line[2:].strip()
                    header_text = markdown_to_html_inline(header_text)
                    flowables.append(Paragraph(f'<b>{header_text}</b>', body_style))
                    flowables.append(Spacer(1, 0.1 * inch))
                    i += 1
                    continue

                # Regular paragraph - might span multiple lines
                para_lines = []
                while i < len(lines):
                    curr_line = lines[i].strip()
                    # Stop at empty line or list/header
                    if not curr_line or curr_line.startswith('- ') or curr_line.startswith('* ') or \
                       curr_line.startswith('#') or curr_line.startswith('```') or curr_line.startswith('~~~'):
                        break
                    para_lines.append(curr_line)
                    i += 1

                if para_lines:
                    para_text = ' '.join(para_lines)
                    para_text = markdown_to_html_inline(para_text)
                    flowables.append(Paragraph(para_text, body_style))
                    flowables.append(Spacer(1, 0.1 * inch))

            return flowables

        def markdown_to_html_inline(text):
            """Convert inline markdown to HTML."""
            if not text:
                return ''

            # Bold
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)

            # Italic
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
            text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)

            # Code
            text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

            # Links
            text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

            return text

        # Build the story (content)
        story = []

        # Add title
        story.append(Paragraph(analysis.title, title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Helper function to add section
        def add_section(title, content):
            if content:
                story.append(Paragraph(title, heading_style))
                section_flowables = parse_markdown_to_flowables(content, body_style, code_style)
                story.extend(section_flowables)
                story.append(Spacer(1, 0.2 * inch))

        # Add all sections
        add_section('Abstract', analysis.abstract)
        add_section('Motivation', analysis.motivation)
        add_section('Contribution', analysis.contribution)
        add_section('Methodology', analysis.how_does_paper_do)
        add_section('Experiments & Results', analysis.what_does_paper_do)
        add_section('Limitations & Challenges', analysis.limitations_challenges)
        add_section('Future Work', analysis.future_work)
        add_section('Conclusion', analysis.conclusion)

        # Build PDF
        doc.build(story)

        return response

    except Exception as e:
        logger.error(f"Error generating PDF for analysis {analysis_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate PDF. Please try again.'
        }, status=500)

