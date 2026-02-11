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

from .services import analyze_paper, analyze_paper_for_ppt
from .models import PaperAnalysis, PPTGeneration
from .ppt_generator import generate_powerpoint, extract_metadata_from_paper

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

        # Reset file pointer after reading (important for database save)
        pdf_file.seek(0)

        # Save to database
        paper_analysis = PaperAnalysis.objects.create(
            user=request.user,
            title=analysis_result.get('title', pdf_file.name.replace('.pdf', '')),
            pdf_file=pdf_file,
            original_filename=pdf_file.name,
            authors=analysis_result.get('authors', ''),
            venue=analysis_result.get('venue', ''),
            year=analysis_result.get('year', ''),
            paper_url=analysis_result.get('paper_url', ''),
            abstract=analysis_result.get('abstract', ''),
            introduction=analysis_result.get('introduction', ''),
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
    context = {
        'max_pdf_size_mb': settings.MAX_PDF_SIZE_MB,
    }
    return render(request, 'generator.html', context)


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
        'introduction': analysis.introduction,
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
def ppt_history(request):
    """
    Display user's PPT generation history.
    """
    ppt_generations = PPTGeneration.objects.filter(user=request.user)

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        ppt_generations = ppt_generations.filter(
            models.Q(title__icontains=search_query) |
            models.Q(original_filename__icontains=search_query) |
            models.Q(abstract__icontains=search_query) |
            models.Q(student_name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(ppt_generations, 12)  # 12 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_count': ppt_generations.count()
    }

    return render(request, 'ppt_history.html', context)


@login_required(login_url='/login/')
def ppt_detail(request, ppt_id):
    """
    View a specific PPT generation.
    """
    ppt = get_object_or_404(PPTGeneration, id=ppt_id, user=request.user)

    # Build analysis result dict from model fields
    analysis_result = {
        'abstract': ppt.abstract,
        'introduction': ppt.introduction,
        'motivation': ppt.motivation,
        'contribution': ppt.contribution,
        'what_does_paper_do': ppt.what_does_paper_do,
        'how_does_paper_do': ppt.how_does_paper_do,
        'future_work': ppt.future_work,
        'conclusion': ppt.conclusion,
    }

    context = {
        'ppt': ppt,
        'analysis_result': analysis_result,
    }

    return render(request, 'ppt_detail.html', context)


@login_required(login_url='/login/')
@require_POST
def delete_ppt(request, ppt_id):
    """
    Delete a specific PPT generation.
    """
    ppt = get_object_or_404(PPTGeneration, id=ppt_id, user=request.user)

    try:
        # Delete the file and record
        if ppt.pdf_file:
            ppt.pdf_file.delete(save=False)
        ppt.delete()

        return JsonResponse({
            'success': True,
            'message': 'PPT generation deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting PPT generation: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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

        # Tighter spacing for list items to match browser view
        list_item_style = ParagraphStyle(
            'ListItem',
            parent=body_style,
            spaceAfter=6,  # Tighter spacing for list items
            leading=14,    # Slightly tighter line height
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

        def parse_markdown_to_flowables(text, body_style, code_style, list_item_style):
            """Parse markdown text and convert to ReportLab flowables with proper nested list support."""
            if not text:
                return []

            flowables = []
            lines = text.split('\n')
            i = 0

            while i < len(lines):
                line = lines[i]

                # Empty line - skip
                if not line.strip():
                    i += 1
                    continue

                stripped = line.strip()

                # Code block (``` or ~~~)
                if stripped.startswith('```') or stripped.startswith('~~~'):
                    i += 1
                    code_lines = []
                    while i < len(lines) and not lines[i].strip().startswith('```') and not lines[i].strip().startswith('~~~'):
                        code_lines.append(lines[i])
                        i += 1
                    code_text = '<br/>'.join(code_lines)
                    flowables.append(Paragraph(f'<code>{code_text}</code>', code_style))
                    i += 1
                    continue

                # Check if this is a list item (bullet or numbered)
                is_bullet = stripped.startswith('- ') or stripped.startswith('* ')
                is_numbered = re.match(r'^(\d+)\.\s+(.*)$', stripped)

                if is_bullet or is_numbered:
                    # Process this list item and any nested items following it
                    # Keep the original marker and add nested items immediately after

                    # Get the base indentation (for this item)
                    base_indent = len(line) - len(line.lstrip())

                    # Add the current list item with tight spacing
                    item_content = stripped
                    if is_bullet:
                        # Remove bullet marker
                        item_content = stripped[2:].strip()
                        item_content = markdown_to_html_inline(item_content)
                        # Add bullet point with list_item_style (tighter spacing)
                        flowables.append(Paragraph(f'• {item_content}', list_item_style))
                    else:
                        # Keep the number with list_item_style
                        item_content = markdown_to_html_inline(stripped)
                        flowables.append(Paragraph(item_content, list_item_style))

                    i += 1

                    # Now look for nested items (indented more than base)
                    while i < len(lines):
                        next_line = lines[i]
                        if not next_line.strip():
                            # Empty line ends the list
                            break

                        next_indent = len(next_line) - len(next_line.lstrip())
                        next_stripped = next_line.strip()

                        # Check if next item is nested (more indented) and is a list item
                        if next_indent > base_indent:
                            next_is_bullet = next_stripped.startswith('- ') or next_stripped.startswith('* ')
                            next_is_numbered = re.match(r'^(\d+)\.\s+(.*)$', next_stripped)

                            if next_is_bullet or next_is_numbered:
                                # This is a nested item - add it with proper indentation and tight spacing
                                nested_indent = 20 + next_indent
                                nested_style = ParagraphStyle(
                                    f'Nested{nested_indent}',
                                    parent=list_item_style,  # Use list_item_style for consistent tight spacing
                                    leftIndent=nested_indent,
                                    spaceBefore=3,
                                    spaceAfter=3
                                )

                                if next_is_bullet:
                                    nested_content = next_stripped[2:].strip()
                                    nested_content = markdown_to_html_inline(nested_content)
                                    flowables.append(Paragraph(f'• {nested_content}', nested_style))
                                else:
                                    nested_content = markdown_to_html_inline(next_stripped)
                                    flowables.append(Paragraph(nested_content, nested_style))

                                i += 1
                            else:
                                # Not a list item, end of nested section
                                break
                        else:
                            # Not indented more, end of this item's nested section
                            # But it might be another top-level list item, so continue to next iteration
                            # Don't increment i, let the outer loop handle it
                            break

                    # Add a small spacer after list group (smaller than before)
                    flowables.append(Spacer(1, 0.05 * inch))
                    continue

                # Header
                if stripped.startswith('###'):
                    header_text = stripped[3:].strip()
                    header_text = markdown_to_html_inline(header_text)
                    flowables.append(Paragraph(f'<b>{header_text}</b>', body_style))
                    flowables.append(Spacer(1, 0.1 * inch))
                    i += 1
                    continue
                elif stripped.startswith('##'):
                    header_text = stripped[2:].strip()
                    header_text = markdown_to_html_inline(header_text)
                    flowables.append(Paragraph(f'<b>{header_text}</b>', body_style))
                    flowables.append(Spacer(1, 0.1 * inch))
                    i += 1
                    continue

                # Regular paragraph - might span multiple lines
                para_lines = []
                while i < len(lines):
                    curr_line = lines[i]
                    curr_stripped = curr_line.strip()
                    # Stop at empty line or list/header/code
                    if not curr_stripped:
                        break
                    if curr_stripped.startswith('- ') or curr_stripped.startswith('* '):
                        break
                    if re.match(r'^\d+\.\s+', curr_stripped):
                        break
                    if curr_stripped.startswith('#') or curr_stripped.startswith('```') or curr_stripped.startswith('~~~'):
                        break
                    para_lines.append(curr_stripped)
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
                section_flowables = parse_markdown_to_flowables(content, body_style, code_style, list_item_style)
                story.extend(section_flowables)
                story.append(Spacer(1, 0.2 * inch))

        # Add all sections
        add_section('Abstract', analysis.abstract)
        add_section('Introduction', analysis.introduction)
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


@login_required(login_url='/login/')
def generate_ppt_from_history(request, analysis_id):
    """
    Generate a PowerPoint presentation from an existing analysis.

    Args:
        analysis_id: ID of the PaperAnalysis record

    Returns:
        HttpResponse: .pptx file download
    """
    analysis = get_object_or_404(PaperAnalysis, id=analysis_id, user=request.user)

    try:
        # Build analysis data dict from model fields
        analysis_data = {
            'abstract': analysis.abstract,
            'introduction': analysis.introduction,
            'motivation': analysis.motivation,
            'contribution': analysis.contribution,
            'what_does_paper_do': analysis.what_does_paper_do,
            'how_does_paper_do': analysis.how_does_paper_do,
            'limitations_challenges': analysis.limitations_challenges,
            'future_work': analysis.future_work,
            'conclusion': analysis.conclusion,
        }

        # Get student info from request (query params) or use existing
        student_name = request.GET.get('student_name', analysis.student_name or 'Your Name')
        student_id = request.GET.get('student_id', analysis.student_id or 'Student ID')

        # Build metadata
        metadata = {
            'title': analysis.title,
            'authors': analysis.authors,
            'venue': analysis.venue,
            'year': analysis.year,
            'paper_url': analysis.paper_url,
            'student_name': student_name,
            'student_id': student_id,
        }

        # Generate PowerPoint
        ppt_buffer = generate_powerpoint(analysis_data, metadata)

        # Create filename
        safe_title = analysis.title.replace(' ', '_').replace('/', '_').replace('\\', '_')[:100]
        filename = f"{safe_title}_presentation.pptx"

        # Create response
        response = HttpResponse(
            ppt_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        logger.error(f"Error generating PPT for analysis {analysis_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate PowerPoint. Please try again.'
        }, status=500)


@login_required(login_url='/login/')
@require_POST
def generate_ppt_from_upload(request):
    """
    Generate a PowerPoint presentation directly from an uploaded PDF.

    This endpoint analyzes the paper using PPT-optimized prompts and generates a PPT in one step,
    with optional student information provided in the request.

    Request parameters:
        - pdf_file: The PDF file to analyze
        - student_name: (optional) Student name for presentation
        - student_id: (optional) Student ID for presentation

    Returns:
        JsonResponse: Success/error response
    """
    if 'pdf_file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No PDF file uploaded. Please select a file.'
        }, status=400)

    pdf_file = request.FILES['pdf_file']
    student_name = request.POST.get('student_name', 'Your Name')
    student_id = request.POST.get('student_id', 'Student ID')

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
        # Analyze the paper using PPT-optimized prompt
        logger.info(f"Analyzing paper for PPT generation: {pdf_file.name}")
        analysis_result = analyze_paper_for_ppt(pdf_file, student_name, student_id)

        logger.info(f"Analysis result keys: {list(analysis_result.keys())}")

        # Extract metadata from paper text
        from .services import extract_text_from_pdf
        paper_text = extract_text_from_pdf(pdf_file)

        # Reset file pointer after reading (important for database save)
        pdf_file.seek(0)

        paper_metadata = extract_metadata_from_paper(paper_text, pdf_file.name)

        # Enhance metadata with LLM-extracted data if available
        if analysis_result.get('title'):
            paper_metadata['title'] = analysis_result['title']
        if analysis_result.get('authors'):
            paper_metadata['authors'] = analysis_result['authors']
        if analysis_result.get('venue'):
            paper_metadata['venue'] = analysis_result['venue']
        if analysis_result.get('year'):
            paper_metadata['year'] = analysis_result['year']
        if analysis_result.get('paper_url'):
            paper_metadata['paper_url'] = analysis_result['paper_url']

        # Add student info
        paper_metadata['student_name'] = student_name
        paper_metadata['student_id'] = student_id

        logger.info(f"Final metadata: title={paper_metadata.get('title')}, student={student_name}")

        # Optionally save to database (if requested)
        save_to_db = request.POST.get('save_to_db', 'false').lower() == 'true'
        ppt_id = None
        if save_to_db:
            ppt_generation = PPTGeneration.objects.create(
                user=request.user,
                title=paper_metadata['title'],
                pdf_file=pdf_file,
                original_filename=pdf_file.name,
                authors=paper_metadata['authors'],
                venue=paper_metadata['venue'],
                year=paper_metadata['year'],
                paper_url=paper_metadata['paper_url'],
                student_name=student_name,
                student_id=student_id,
                abstract=analysis_result.get('abstract', ''),
                introduction=analysis_result.get('introduction', ''),
                motivation=analysis_result.get('motivation', ''),
                contribution=analysis_result.get('contribution', ''),
                what_does_paper_do=analysis_result.get('what_does_paper_do', ''),
                how_does_paper_do=analysis_result.get('how_does_paper_do', ''),
                future_work=analysis_result.get('future_work', ''),
                conclusion=analysis_result.get('conclusion', ''),
                analysis_data=analysis_result
            )
            ppt_id = ppt_generation.id
            logger.info(f"Saved PPT generation to DB with ID: {ppt_id}")

        # Generate PowerPoint
        logger.info("Generating PowerPoint...")
        ppt_buffer = generate_powerpoint(analysis_result, paper_metadata)

        # Create filename
        safe_title = paper_metadata['title'].replace(' ', '_').replace('/', '_').replace('\\', '_')[:100]
        filename = f"{safe_title}_presentation.pptx"

        # Create response
        response = HttpResponse(
            ppt_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # If saved to DB, include the PPT ID in response header
        if ppt_id:
            response['X-PPT-ID'] = str(ppt_id)

        logger.info(f"PPT generated successfully: {filename}, size={len(ppt_buffer.getvalue())} bytes")
        return response

    except ValueError as e:
        # Validation error
        logger.error(f"Validation error generating PPT: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        # Unexpected error
        logger.error(f"Error generating PPT from upload: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f"Failed to generate presentation: {str(e)}"
        }, status=500)

