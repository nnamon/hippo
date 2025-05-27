#!/usr/bin/env python3
"""
Coverage analysis script for Hippo bot project.
Generates detailed coverage reports and metrics.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any


def run_tests_with_coverage():
    """Run tests and generate coverage reports."""
    print("🧪 Running tests with coverage analysis...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "--cov=src",
            "--cov-report=xml",
            "--cov-report=html",
            "--cov-report=json",
            "--cov-report=term-missing",
            "--cov-branch",
            "--verbose"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Tests completed successfully!")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Tests failed!")
        print(e.stdout)
        print(e.stderr)
        return False


def analyze_coverage_data():
    """Analyze coverage data and generate detailed metrics."""
    coverage_json_path = Path("coverage.json")
    
    if not coverage_json_path.exists():
        print("❌ Coverage JSON file not found. Run tests first.")
        return None
    
    with open(coverage_json_path, 'r') as f:
        coverage_data = json.load(f)
    
    return coverage_data


def generate_coverage_summary(coverage_data: Dict[str, Any]):
    """Generate a detailed coverage summary."""
    if not coverage_data:
        return
    
    print("\n📊 COVERAGE ANALYSIS SUMMARY")
    print("=" * 50)
    
    # Overall coverage
    totals = coverage_data.get('totals', {})
    covered_lines = totals.get('covered_lines', 0)
    num_statements = totals.get('num_statements', 0)
    missing_lines = totals.get('missing_lines', 0)
    excluded_lines = totals.get('excluded_lines', 0)
    
    if num_statements > 0:
        coverage_percent = (covered_lines / num_statements) * 100
        print(f"📈 Overall Coverage: {coverage_percent:.1f}%")
        print(f"📋 Total Statements: {num_statements}")
        print(f"✅ Covered Lines: {covered_lines}")
        print(f"❌ Missing Lines: {missing_lines}")
        print(f"🚫 Excluded Lines: {excluded_lines}")
    
    # Per-file breakdown
    print("\n📂 PER-FILE COVERAGE BREAKDOWN")
    print("-" * 50)
    
    files = coverage_data.get('files', {})
    file_stats = []
    
    for file_path, file_data in files.items():
        if not file_path.startswith('src/'):
            continue
            
        summary = file_data.get('summary', {})
        file_covered = summary.get('covered_lines', 0)
        file_statements = summary.get('num_statements', 0)
        
        if file_statements > 0:
            file_percent = (file_covered / file_statements) * 100
            file_stats.append((file_path, file_percent, file_covered, file_statements))
    
    # Sort by coverage percentage
    file_stats.sort(key=lambda x: x[1], reverse=True)
    
    for file_path, percent, covered, total in file_stats:
        status = "🟢" if percent >= 80 else "🟡" if percent >= 60 else "🔴"
        print(f"{status} {file_path:<40} {percent:>6.1f}% ({covered}/{total})")
    
    # Coverage recommendations
    print("\n💡 COVERAGE RECOMMENDATIONS")
    print("-" * 50)
    
    low_coverage_files = [f for f in file_stats if f[1] < 70]
    if low_coverage_files:
        print("Files needing attention (< 70% coverage):")
        for file_path, percent, _, _ in low_coverage_files:
            print(f"  • {file_path}: {percent:.1f}%")
    else:
        print("🎉 All files have good coverage (≥ 70%)!")
    
    # Missing line analysis
    print("\n🔍 MISSING LINES ANALYSIS")
    print("-" * 50)
    
    total_missing = 0
    for file_path, file_data in files.items():
        if not file_path.startswith('src/'):
            continue
            
        missing_lines = file_data.get('missing_lines', [])
        if missing_lines:
            total_missing += len(missing_lines)
            print(f"📁 {file_path}:")
            
            # Group consecutive lines
            line_groups = []
            current_group = [missing_lines[0]] if missing_lines else []
            
            for line in missing_lines[1:]:
                if line == current_group[-1] + 1:
                    current_group.append(line)
                else:
                    line_groups.append(current_group)
                    current_group = [line]
            
            if current_group:
                line_groups.append(current_group)
            
            for group in line_groups:
                if len(group) == 1:
                    print(f"   Line {group[0]}")
                else:
                    print(f"   Lines {group[0]}-{group[-1]}")
    
    print(f"\n📊 Total missing lines across all files: {total_missing}")
    
    return coverage_data


def generate_badge_data(coverage_data: Dict[str, Any]):
    """Generate badge data for README."""
    if not coverage_data:
        return
    
    totals = coverage_data.get('totals', {})
    covered_lines = totals.get('covered_lines', 0)
    num_statements = totals.get('num_statements', 0)
    
    if num_statements > 0:
        coverage_percent = (covered_lines / num_statements) * 100
        
        # Determine badge color
        if coverage_percent >= 90:
            color = "brightgreen"
        elif coverage_percent >= 80:
            color = "green"
        elif coverage_percent >= 70:
            color = "yellowgreen"
        elif coverage_percent >= 60:
            color = "yellow"
        else:
            color = "red"
        
        badge_url = f"https://img.shields.io/badge/coverage-{coverage_percent:.1f}%25-{color}"
        
        print("\n🏷️ COVERAGE BADGE")
        print("-" * 50)
        print("Add this to your README.md:")
        print(f"![Coverage]({badge_url})")
        print(f"\nMarkdown code:")
        print(f"```markdown")
        print(f"![Coverage]({badge_url})")
        print(f"```")


def main():
    """Main function."""
    print("🦛 Hippo Bot Coverage Analysis")
    print("=" * 50)
    
    # Run tests
    if not run_tests_with_coverage():
        sys.exit(1)
    
    # Analyze coverage
    coverage_data = analyze_coverage_data()
    if coverage_data:
        generate_coverage_summary(coverage_data)
        generate_badge_data(coverage_data)
    
    print("\n✨ Coverage analysis complete!")
    print("📁 Check htmlcov/index.html for detailed HTML report")


if __name__ == "__main__":
    main()