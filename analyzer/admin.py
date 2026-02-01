from django.contrib import admin
from .models import PaperAnalysis


@admin.register(PaperAnalysis)
class PaperAnalysisAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'original_filename', 'created_date', 'file_size_mb']
    list_filter = ['created_date', 'user']
    search_fields = ['title', 'original_filename', 'abstract']
    readonly_fields = ['created_date', 'updated_date', 'file_size_mb']
    date_hierarchy = 'created_date'

    fieldsets = (
        ('Paper Information', {
            'fields': ('user', 'title', 'pdf_file', 'original_filename')
        }),
        ('Analysis Results', {
            'fields': ('abstract', 'motivation', 'contribution', 'what_does_paper_do',
                      'how_does_paper_do', 'limitations_challenges', 'future_work', 'conclusion')
        }),
        ('Additional Data', {
            'fields': ('analysis_data',)
        }),
        ('Metadata', {
            'fields': ('created_date', 'updated_date', 'file_size_mb'),
            'classes': ('collapse',)
        }),
    )
