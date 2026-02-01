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


class PaperAnalysis(models.Model):
    """
    Store paper analysis results including the PDF file and analysis data.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paper_analyses')

    # Paper information
    title = models.CharField(max_length=500, blank=True, help_text="Paper title extracted from filename or content")
    pdf_file = models.FileField(upload_to=upload_paper_to, max_length=500, help_text="Uploaded PDF file")
    original_filename = models.CharField(max_length=255, help_text="Original filename of uploaded PDF")

    # Analysis results - stored as individual fields for easy access
    abstract = models.TextField(blank=True, help_text="Paper abstract")
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
