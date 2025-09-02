#!/usr/bin/env python3
"""
Setup script for the Django API Gateway
This script automates the initial setup process.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def create_env_file():
    """Create .env file from template."""
    if not os.path.exists('.env'):
        print("Creating .env file...")
        try:
            with open('env.example', 'r') as f:
                content = f.read()
            
            # Generate a secret key
            import secrets
            import string
            secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(50))
            content = content.replace('your-secret-key-here', secret_key)
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("✓ .env file created with generated secret key")
            return True
        except Exception as e:
            print(f"✗ Failed to create .env file: {e}")
            return False
    else:
        print("✓ .env file already exists")
        return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check if pip is available
    try:
        subprocess.run([sys.executable, '-m', 'pip', '--version'], check=True, capture_output=True)
        print("✓ pip is available")
    except subprocess.CalledProcessError:
        print("✗ pip is not available")
        return False
    
    return True


def install_dependencies():
    """Install Python dependencies."""
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    )


def run_migrations():
    """Run Django migrations."""
    return run_command(
        "python manage.py migrate",
        "Running database migrations"
    )


def create_superuser():
    """Create a superuser account."""
    print("Creating superuser account...")
    print("Please enter the following information:")
    
    username = input("Username (default: admin): ").strip() or "admin"
    email = input("Email (optional): ").strip()
    password = input("Password: ").strip()
    
    if not password:
        print("✗ Password is required")
        return False
    
    # Create superuser using Django management command
    command = f"python manage.py createsuperuser --noinput --username {username}"
    if email:
        command += f" --email {email}"
    
    # Set password using Django shell
    password_script = f"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_gateway.settings')
django.setup()
from django.contrib.auth.models import User
user = User.objects.get(username='{username}')
user.set_password('{password}')
user.save()
print('Superuser created successfully')
"""
    
    try:
        # Create superuser
        subprocess.run(command, shell=True, check=True, capture_output=True)
        
        # Set password
        subprocess.run(
            f"{sys.executable} -c \"{password_script}\"",
            shell=True, check=True
        )
        
        print(f"✓ Superuser '{username}' created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create superuser: {e}")
        return False


def setup_sample_data():
    """Set up sample data."""
    return run_command(
        "python manage.py setup_gateway --all",
        "Setting up sample data"
    )


def main():
    """Main setup function."""
    print("Django API Gateway Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("✗ Please run this script from the project root directory")
        return False
    
    steps = [
        ("Checking dependencies", check_dependencies),
        ("Creating environment file", create_env_file),
        ("Installing dependencies", install_dependencies),
        ("Running migrations", run_migrations),
        ("Setting up sample data", setup_sample_data),
    ]
    
    # Run setup steps
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"✗ Setup failed at: {step_name}")
            return False
    
    # Ask about creating superuser
    print("\n" + "=" * 50)
    create_admin = input("Would you like to create a superuser account? (y/n): ").lower().strip()
    if create_admin in ['y', 'yes']:
        if not create_superuser():
            print("⚠️  Superuser creation failed, but you can create one manually later")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start Redis server (for rate limiting)")
    print("2. Run the development server: python manage.py runserver")
    print("3. Access the admin interface at: http://localhost:8000/admin/")
    print("4. Test the API Gateway: python test_api_gateway.py")
    print("\nFor more information, see the README.md file")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
