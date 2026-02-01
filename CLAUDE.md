# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Paper Analyzer is a Django 6.0.1 web application for analyzing academic papers. The project uses Python 3.14+ and Django with a modern frontend stack combining Vue 3, Tailwind CSS, and HTMX for dynamic interactions.

## Environment Setup

**Required Environment Variables:**
The application requires a `.env` file in the project root with:
- `DJANGO_SECRET_KEY` - Django secret key (required, will raise ValueError if not set)
- `DJANGO_DEBUG` - Debug mode (default: False)

**Virtual Environment:**
The project uses a virtual environment at `.venv/`. Activate it before running commands:
```bash
# Windows (Command Prompt)
.venv\Scripts\activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Unix/macOS
source .venv/bin/activate
```

## Common Commands

**Development Server:**
```bash
python manage.py runserver
```

**Database Migrations:**
```bash
python manage.py makemigrations      # Create new migrations
python manage.py migrate             # Apply migrations
```

**Django Admin:**
```bash
python manage.py createsuperuser     # Create admin user
python manage.py shell               # Open Django shell
```

**Testing:**
```bash
python manage.py test                # Run all tests
python manage.py test analyzer       # Run tests for analyzer app
```

**Project Dependencies:**
Dependencies are managed via `uv` (implied by pyproject.toml structure):
```bash
uv sync                              # Install dependencies
```

## Architecture

### Project Structure

```
paper-analyzer/
├── paper_analyzer/          # Main Django project configuration
│   ├── settings.py          # Django settings with environment-based config
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py              # WSGI application entry point
├── analyzer/                # Main Django app for paper analysis
│   ├── models.py            # Database models (currently empty)
│   ├── views.py             # View logic (currently empty)
│   └── admin.py             # Admin configuration
├── templates/               # Global templates directory
│   ├── base.html            # Base template with Vue 3, Tailwind, HTMX
│   ├── layout.html          # Layout template (extends base.html)
│   ├── analyzer.html        # Analyzer page template
│   ├── login.html           # Login page template
│   └── generator.html       # Generator page template
└── manage.py                # Django management script
```

### Key Architectural Patterns

**Template Hierarchy:**
- `base.html` - Root template providing:
  - Vue 3 (CDN)
  - Tailwind CSS v4 (CDN)
  - HTMX 2.0.8 (CDN)
  - Base block structure: `{% block title %}`, `{% block style %}`, `{% block content %}`, `{% block script %}`, `{% block extra_head %}`, `{% block extra_body %}`
  - Root div with `id="app"` for Vue mounting
- `layout.html` - Intermediate layout (extends base.html)
- Page templates (analyzer.html, login.html, generator.html) - Extend layout.html

**Settings Configuration:**
- Uses `python-dotenv` for environment variable loading
- `ALLOWED_HOSTS` set to `["*"]` for development
- Templates configured to use global `templates/` directory
- SQLite database by default (`db.sqlite3`)
- Timezone set to `Asia/Shanghai`

**Apps:**
- `analyzer` - Custom app for paper analysis functionality (currently scaffolded)
- Standard Django apps: admin, auth, contenttypes, sessions, messages, staticfiles

### Current State

The project is in early development:
- Models and views in the `analyzer` app are empty/placeholder
- Template structure is established but content is minimal
- URL routing is minimal (only admin URLs configured)
- No database models defined yet

## Development Notes

**Adding New URLs:**
URL patterns are defined in `paper_analyzer/urls.py`. Include app-specific URL configurations using Django's `include()` function when adding routes to the analyzer app.

**Template Organization:**
All templates are stored in the global `templates/` directory rather than app-specific template directories. When adding new views, reference templates directly by filename (e.g., `'analyzer.html'`).

**Frontend Stack:**
The application uses CDN-hosted versions of Vue 3, Tailwind CSS, and HTMX. When adding interactive features:
- Use Vue 3 Composition API within `{% block script %}` blocks
- Leverage Tailwind utility classes for styling
- Use HTMX attributes for server-driven dynamic updates where appropriate
