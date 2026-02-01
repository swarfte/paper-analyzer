#!/usr/bin/env python
"""
Setup script for Paper Analyzer project.

This script helps new developers quickly set up the development environment.
Run with: uv run setup.py
"""

import os
import sys
import shutil
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a header with styling."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗{Colors.ENDC} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠{Colors.ENDC} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ{Colors.ENDC} {text}")


def check_env_file() -> bool:
    """Check if .env file exists, create from .env.example if not."""
    print_header("Step 1: Environment Configuration")

    env_path = Path(".env")
    env_example_path = Path(".env.example")

    if env_path.exists():
        print_success(".env file already exists")
        return True

    if not env_example_path.exists():
        print_error(".env.example not found!")
        print_info("Please ensure .env.example exists in the project root.")
        return False

    print_warning(".env file not found")
    print_info("Creating .env from .env.example...")

    try:
        shutil.copy(env_example_path, env_path)
        print_success("Created .env file from .env.example")
        print_warning("\nIMPORTANT: Please update the following values in .env:")
        print("  - DJANGO_SECRET_KEY (required)")
        print("  - OPENROUTER_API_KEY (for paper analysis)")
        print("  - ADMIN_USERNAME (for admin account)")
        print("  - ADMIN_PASSWORD (for admin account)")

        response = input("\nHave you finished updating the .env file? (y/n): ").strip().lower()
        if response != 'y':
            print_warning("Please update .env file and run setup.py again.")
            return False

        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False


def validate_environment() -> bool:
    """Validate required environment variables."""
    print_header("Step 2: Validating Environment Variables")

    from dotenv import load_dotenv
    load_dotenv()

    required_vars = {
        'DJANGO_SECRET_KEY': 'Django secret key',
    }

    optional_vars = {
        'OPENROUTER_API_KEY': 'OpenRouter API key (required for paper analysis)',
        'ADMIN_USERNAME': 'Admin username (required for creating admin user)',
        'ADMIN_PASSWORD': 'Admin password (required for creating admin user)',
    }

    all_valid = True

    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            print_error(f"{var} ({description}) - {Colors.FAIL}MISSING{Colors.ENDC}")
            all_valid = False
        else:
            print_success(f"{var} is set")

    # Check optional variables
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if not value:
            print_warning(f"{var} not set ({description})")
        else:
            print_success(f"{var} is set")

    if not all_valid:
        print_error("\nRequired environment variables are missing!")
        print_info("Please update your .env file with the required values.")
        return False

    return True


def run_migrations() -> bool:
    """Run Django database migrations."""
    print_header("Step 3: Running Database Migrations")

    try:
        import django
        from django.core.management import execute_from_command_line

        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paper_analyzer.settings')
        django.setup()

        print_info("Running migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        print_success("Database migrations completed")
        return True

    except Exception as e:
        print_error(f"Failed to run migrations: {e}")
        return False


def create_superuser() -> bool:
    """Create Django superuser from environment variables."""
    print_header("Step 4: Creating Admin User")

    from dotenv import load_dotenv
    load_dotenv()

    username = os.getenv('ADMIN_USERNAME')
    password = os.getenv('ADMIN_PASSWORD')

    if not username or not password:
        print_warning("ADMIN_USERNAME or ADMIN_PASSWORD not set")
        print_info("Skipping admin user creation.")
        print_info("You can create an admin user later with: python manage.py createsuperuser")
        return True

    try:
        import django
        from django.contrib.auth import get_user_model
        from django.core.management import execute_from_command_line

        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paper_analyzer.settings')
        django.setup()

        User = get_user_model()

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print_warning(f"User '{username}' already exists")
            response = input("Do you want to reset the password? (y/n): ").strip().lower()
            if response == 'y':
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                print_success(f"Password updated for user '{username}'")
            return True

        # Create new superuser
        print_info(f"Creating admin user '{username}'...")
        User.objects.create_superuser(username=username, password=password)
        print_success(f"Admin user '{username}' created successfully")
        return True

    except Exception as e:
        print_error(f"Failed to create admin user: {e}")
        return False


def collect_static() -> bool:
    """Collect static files."""
    print_header("Step 5: Collecting Static Files")

    try:
        from django.core.management import execute_from_command_line

        print_info("Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print_success("Static files collected")
        return True

    except Exception as e:
        print_error(f"Failed to collect static files: {e}")
        return False


def print_completion_message():
    """Print setup completion message."""
    print_header("Setup Complete!")
    print_success("Your Paper Analyzer environment is ready!\n")

    print("Next steps:")
    print("  1. Start the development server:")
    print(f"     {Colors.OKCYAN}uv run manage.py runserver{Colors.ENDC}")
    print("\n  2. Open your browser and navigate to:")
    print(f"     {Colors.OKCYAN}http://localhost:8000{Colors.ENDC}")
    print("\n  3. Access the admin panel at:")
    print(f"     {Colors.OKCYAN}http://localhost:8000/admin/{Colors.ENDC}")
    print("\n  4. To create additional admin users:")
    print(f"     {Colors.OKCYAN}uv run manage.py createsuperuser{Colors.ENDC}\n")


def main():
    """Main setup function."""
    print_header("Paper Analyzer - Environment Setup")
    print("This script will guide you through the setup process.\n")

    steps = [
        check_env_file,
        validate_environment,
        run_migrations,
        create_superuser,
        collect_static,
    ]

    for step in steps:
        if not step():
            print_error(f"\nSetup failed at step: {step.__name__}")
            print_info("Please fix the issues above and run setup.py again.")
            sys.exit(1)

    print_completion_message()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)
