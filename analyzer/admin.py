from django.contrib import admin
from .models import PaperAnalysis, PPTGeneration


@admin.register(PaperAnalysis)
class PaperAnalysisAdmin(admin.ModelAdmin):
    """Admin interface for Paper Analyzer feature - research analysis"""
    list_display = ['user', 'title', 'original_filename', 'created_date', 'file_size_mb']
    list_filter = ['created_date', 'user']
    search_fields = ['title', 'original_filename', 'abstract']
    readonly_fields = ['created_date', 'updated_date', 'file_size_mb']
    date_hierarchy = 'created_date'

    fieldsets = (
        ('Paper Information', {
            'fields': ('user', 'title', 'pdf_file', 'original_filename', 'authors', 'venue', 'year', 'paper_url')
        }),
        ('Analysis Results', {
            'fields': ('abstract', 'introduction', 'motivation', 'contribution', 'what_does_paper_do',
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


@admin.register(PPTGeneration)
class PPTGenerationAdmin(admin.ModelAdmin):
    """Admin interface for PPT Generator feature - presentation generation"""
    list_display = ['user', 'title', 'original_filename', 'student_name', 'student_id', 'created_date', 'file_size_mb']
    list_filter = ['created_date', 'user', 'venue', 'year']
    search_fields = ['title', 'original_filename', 'student_name', 'authors']
    readonly_fields = ['created_date', 'updated_date', 'file_size_mb']
    date_hierarchy = 'created_date'

    fieldsets = (
        ('Paper Information', {
            'fields': ('user', 'title', 'pdf_file', 'original_filename', 'authors', 'venue', 'year', 'paper_url')
        }),
        ('Student Information', {
            'fields': ('student_name', 'student_id')
        }),
        ('PPT-Optimized Analysis', {
            'fields': ('abstract', 'introduction', 'motivation', 'contribution', 'what_does_paper_do',
                      'how_does_paper_do', 'future_work', 'conclusion')
        }),
        ('Additional Data', {
            'fields': ('analysis_data',)
        }),
        ('Metadata', {
            'fields': ('created_date', 'updated_date', 'file_size_mb'),
            'classes': ('collapse',)
        }),
    )
