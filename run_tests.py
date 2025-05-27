#!/usr/bin/env python3
"""
Test runner script for Hippo bot.
"""

import os
import sys
import subprocess
import argparse


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} passed")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Hippo bot tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--docker", action="store_true", help="Run tests in Docker")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--coverage-analysis", action="store_true", help="Run detailed coverage analysis")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--security", action="store_true", help="Run security checks")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    
    args = parser.parse_args()
    
    # If no specific tests specified, run unit tests
    if not any([args.unit, args.integration, args.docker, args.lint, args.security, args.coverage_analysis, args.all]):
        args.unit = True
    
    success = True
    
    # Set Python path
    os.environ['PYTHONPATH'] = os.path.join(os.getcwd(), 'src')
    
    print("🦛 Hippo Bot Test Runner")
    print("=" * 40)
    
    if args.all or args.lint:
        if not run_command("flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503", "Linting checks"):
            success = False
    
    if args.all or args.security:
        if not run_command("bandit -r src/ -ll", "Security analysis"):
            success = False
        if not run_command("safety check", "Dependency vulnerability check"):
            success = False
    
    if args.all or args.unit:
        cmd = "pytest tests/ -v --tb=short"
        if args.coverage or args.all:
            cmd += " --cov=src --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml --cov-report=json --cov-branch --cov-fail-under=55"
        if not run_command(cmd, "Unit tests"):
            success = False
    
    if args.all or args.integration:
        integration_cmd = """
python -c "
import asyncio
import sys
import tempfile
import os

async def test_full_integration():
    sys.path.append('src')
    from database.models import DatabaseManager
    from content.manager import ContentManager
    from bot.reminder_system import ReminderSystem
    
    # Test database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    db = DatabaseManager(db_path)
    await db.initialize()
    
    # Test content manager
    content_manager = ContentManager()
    assert len(content_manager.fallback_poems) > 0
    
    # Test reminder system
    reminder_system = ReminderSystem(db, content_manager)
    
    await db.close()
    os.unlink(db_path)
    print('Integration test passed!')

asyncio.run(test_full_integration())
"
        """
        if not run_command(integration_cmd, "Integration tests"):
            success = False
    
    if args.all or args.docker:
        if not run_command("docker build -f Dockerfile.test -t hippo-test:latest .", "Docker test image build"):
            success = False
        else:
            if not run_command("docker run --rm hippo-test:latest", "Docker tests"):
                success = False
    
    if args.coverage_analysis or args.all:
        if not run_command("python coverage_analysis.py", "Detailed coverage analysis"):
            success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())