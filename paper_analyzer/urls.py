"""
URL configuration for paper_analyzer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
import os
from analyzer.views import (
    custom_login, custom_logout, analyzer, generator, analyze_pdf,
    analysis_history, analysis_detail, delete_analysis, analysis_list_api
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('analyzer/', analyzer, name='analyzer'),
    path('analyzer/analyze/', analyze_pdf, name='analyze_pdf'),
    path('generator/', generator, name='generator'),
    path('history/', analysis_history, name='analysis_history'),
    path('history/<int:analysis_id>/', analysis_detail, name='analysis_detail'),
    path('history/<int:analysis_id>/delete/', delete_analysis, name='delete_analysis'),
    path('api/history/', analysis_list_api, name='analysis_list_api'),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files from the static directory in development
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))
