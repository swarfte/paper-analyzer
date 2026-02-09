from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


def upload_paper_to(instance, filename):
    """Upload path for paper PDFs with timestamp to avoid duplicates"""
    # Split filename and extension
    name, ext = os.path.splitext(filename)

    # Get current timestamp including seconds
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

    # Create new filename: original_name_timestamp.ext
    new_filename = f"{name}_{timestamp}{ext}"

    return os.path.join('papers', str(instance.user.id), new_filename)


def upload_ppt_paper_to(instance, filename):
    """Upload path for PPT generator paper PDFs with timestamp"""
    # Split filename and extension
    name, ext = os.path.splitext(filename)

    # Get current timestamp including seconds
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

    # Create new filename: original_name_timestamp.ext
    new_filename = f"{name}_{timestamp}{ext}"

    return os.path.join('ppt_papers', str(instance.user.id), new_filename)


class PaperAnalysis(models.Model):
    """
    Store paper analysis results for the Paper Analyzer feature.
    Used for research understanding and detailed analysis.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paper_analyses')

    # Paper information
    title = models.CharField(max_length=500, blank=True, help_text="Paper title extracted from filename or content")
    pdf_file = models.FileField(upload_to=upload_paper_to, max_length=500, help_text="Uploaded PDF file")
    original_filename = models.CharField(max_length=255, help_text="Original filename of uploaded PDF")

    # Additional metadata
    authors = models.TextField(blank=True, help_text="Paper authors (comma-separated)")
    venue = models.CharField(max_length=255, blank=True, help_text="Publication venue (journal/conference)")
    year = models.CharField(max_length=10, blank=True, help_text="Publication year")
    paper_url = models.URLField(blank=True, help_text="Paper download URL")

    # Analysis results - stored as individual fields for easy access
    abstract = models.TextField(blank=True, help_text="Paper abstract")
    introduction = models.TextField(blank=True, help_text="Introduction and related work")
    motivation = models.TextField(blank=True, help_text="Research motivation")
    contribution = models.TextField(blank=True, help_text="Key contributions")
    what_does_paper_do = models.TextField(blank=True, help_text="Experiments and results")
    how_does_paper_do = models.TextField(blank=True, help_text="Methodology and framework")
    limitations_challenges = models.TextField(blank=True, help_text="Limitations and challenges")
    future_work = models.TextField(blank=True, help_text="Future work suggestions")
    conclusion = models.TextField(blank=True, help_text="Conclusion")

    # Full analysis data as JSON (for flexibility)
    analysis_data = models.JSONField(default=dict, blank=True, help_text="Complete analysis as JSON")

    # Metadata
    created_date = models.DateTimeField(auto_now_add=True, help_text="When the analysis was created")
    updated_date = models.DateTimeField(auto_now=True, help_text="When the analysis was last updated")

    class Meta:
        ordering = ['-created_date']
        verbose_name = "Paper Analysis"
        verbose_name_plural = "Paper Analyses"

    def __str__(self):
        return f"{self.user.username} - {self.title or self.original_filename} ({self.created_date.strftime('%Y-%m-%d %H:%M')})"

    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.pdf_file and hasattr(self.pdf_file, 'size'):
            return round(self.pdf_file.size / (1024 * 1024), 2)
        return 0


class PPTGeneration(models.Model):
    """
    Store PPT generation history for the PPT Generator feature.
    Used for generating PowerPoint presentations from research papers.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ppt_generations')

    # Paper information
    title = models.CharField(max_length=500, blank=True, help_text="Paper title extracted from filename or content")
    pdf_file = models.FileField(upload_to=upload_ppt_paper_to, max_length=500, help_text="Uploaded PDF file")
    original_filename = models.CharField(max_length=255, help_text="Original filename of uploaded PDF")

    # Metadata for presentation
    authors = models.TextField(blank=True, help_text="Paper authors (comma-separated)")
    venue = models.CharField(max_length=255, blank=True, help_text="Publication venue (journal/conference)")
    year = models.CharField(max_length=10, blank=True, help_text="Publication year")
    paper_url = models.URLField(blank=True, help_text="Paper download URL")
    student_name = models.CharField(max_length=255, blank=True, help_text="Student name for presentation")
    student_id = models.CharField(max_length=50, blank=True, help_text="Student ID for presentation")

    # PPT-optimized analysis results
    abstract = models.TextField(blank=True, help_text="Paper abstract for speaker notes")
    introduction = models.TextField(blank=True, help_text="Introduction and related work (slide-ready)")
    motivation = models.TextField(blank=True, help_text="Research motivation (slide-ready)")
    contribution = models.TextField(blank=True, help_text="Key contributions (slide-ready)")
    what_does_paper_do = models.TextField(blank=True, help_text="Experiments and results (slide-ready)")
    how_does_paper_do = models.TextField(blank=True, help_text="Methodology and framework (slide-ready)")
    future_work = models.TextField(blank=True, help_text="Future work suggestions (slide-ready)")
    conclusion = models.TextField(blank=True, help_text="Conclusion (slide-ready)")

    # Full analysis data as JSON (for flexibility)
    analysis_data = models.JSONField(default=dict, blank=True, help_text="Complete PPT-optimized analysis as JSON")

    # Metadata
    created_date = models.DateTimeField(auto_now_add=True, help_text="When the PPT was generated")
    updated_date = models.DateTimeField(auto_now=True, help_text="When the record was last updated")

    class Meta:
        ordering = ['-created_date']
        verbose_name = "PPT Generation"
        verbose_name_plural = "PPT Generations"

    def __str__(self):
        return f"{self.user.username} - {self.title or self.original_filename} PPT ({self.created_date.strftime('%Y-%m-%d %H:%M')})"

    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.pdf_file and hasattr(self.pdf_file, 'size'):
            return round(self.pdf_file.size / (1024 * 1024), 2)
        return 0
