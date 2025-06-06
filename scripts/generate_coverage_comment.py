#!/usr/bin/env python3
"""
Generate coverage comment for GitHub PR.
Reads coverage data and creates a formatted comment with coverage information.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional


def load_coverage_data() -> Optional[Dict[str, Any]]:
    """Load coverage data from JSON file."""
    coverage_file = Path("coverage.json")
    if not coverage_file.exists():
        print("❌ Coverage JSON file not found", file=sys.stderr)
        print(f"Current directory: {os.getcwd()}", file=sys.stderr)
        print(f"Files in directory: {list(Path('.').glob('*'))}", file=sys.stderr)
        return None
    
    try:
        with open(coverage_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading coverage data: {e}", file=sys.stderr)
        return None


def get_coverage_emoji(percentage: float) -> str:
    """Get emoji based on coverage percentage."""
    if percentage >= 90:
        return "🟢"
    elif percentage >= 80:
        return "🟡"
    elif percentage >= 70:
        return "🟠"
    else:
        return "🔴"


def get_coverage_color(percentage: float) -> str:
    """Get color for coverage badge."""
    if percentage >= 90:
        return "brightgreen"
    elif percentage >= 80:
        return "green"
    elif percentage >= 70:
        return "yellowgreen"
    elif percentage >= 60:
        return "yellow"
    else:
        return "red"


def generate_file_coverage_table(coverage_data: Dict[str, Any]) -> str:
    """Generate file-by-file coverage table."""
    files = coverage_data.get('files', {})
    
    table_rows = []
    for file_path, file_data in files.items():
        if not file_path.startswith('src/'):
            continue
            
        summary = file_data.get('summary', {})
        covered = summary.get('covered_lines', 0)
        total = summary.get('num_statements', 0)
        
        if total == 0:
            continue
            
        percentage = (covered / total) * 100
        emoji = get_coverage_emoji(percentage)
        
        table_rows.append(f"| {emoji} `{file_path}` | {percentage:.1f}% | {covered}/{total} |")
    
    # Sort by coverage percentage
    table_rows.sort(key=lambda x: float(x.split('|')[2].strip().rstrip('%')), reverse=True)
    
    table = """| File | Coverage | Lines |
|------|----------|-------|
""" + "\n".join(table_rows)
    
    return table


def generate_coverage_comment(coverage_data: Dict[str, Any]) -> str:
    """Generate the complete coverage comment."""
    totals = coverage_data.get('totals', {})
    covered_lines = totals.get('covered_lines', 0)
    num_statements = totals.get('num_statements', 0)
    missing_lines = totals.get('missing_lines', 0)
    
    if num_statements == 0:
        return "❌ No coverage data available"
    
    overall_percentage = (covered_lines / num_statements) * 100
    emoji = get_coverage_emoji(overall_percentage)
    color = get_coverage_color(overall_percentage)
    
    # Generate badge URL
    badge_url = f"https://img.shields.io/badge/coverage-{overall_percentage:.1f}%25-{color}"
    
    # Get git info for context
    commit_sha = os.environ.get('GITHUB_SHA', 'unknown')[:7]
    pr_number = os.environ.get('GITHUB_REF', '').split('/')[-2] if 'pull' in os.environ.get('GITHUB_REF', '') else 'unknown'
    
    comment = f"""## {emoji} Coverage Report

![Coverage Badge]({badge_url})

### 📊 Overall Coverage: {overall_percentage:.1f}%

- **Lines Covered**: {covered_lines:,} / {num_statements:,}
- **Lines Missing**: {missing_lines:,}
- **Commit**: `{commit_sha}`

### 📁 File Coverage Breakdown

{generate_file_coverage_table(coverage_data)}

### 💡 Coverage Summary

"""

    # Add coverage recommendations
    low_coverage_files = []
    files = coverage_data.get('files', {})
    
    for file_path, file_data in files.items():
        if not file_path.startswith('src/'):
            continue
            
        summary = file_data.get('summary', {})
        covered = summary.get('covered_lines', 0)
        total = summary.get('num_statements', 0)
        
        if total > 0:
            percentage = (covered / total) * 100
            if percentage < 70:
                low_coverage_files.append((file_path, percentage))
    
    if low_coverage_files:
        comment += "**Files needing attention (< 70% coverage):**\n"
        for file_path, percentage in sorted(low_coverage_files, key=lambda x: x[1]):
            comment += f"- `{file_path}`: {percentage:.1f}%\n"
    else:
        comment += "🎉 All files have good coverage (≥ 70%)!\n"
    
    comment += f"""
### 🔗 Useful Links

- 📊 [View detailed HTML report](../../actions) (in artifacts)
- 📈 [Coverage trends](https://codecov.io/gh/{os.environ.get('GITHUB_REPOSITORY', '')})
- 🛠️ [Run tests locally](../../blob/{os.environ.get('GITHUB_HEAD_REF', 'main')}/COVERAGE.md#how-to-run-coverage-analysis)

---
*This comment was automatically generated by the coverage analysis workflow.*
"""
    
    return comment


def generate_coverage_diff_comment(coverage_data: Dict[str, Any], base_coverage: Optional[float] = None) -> str:
    """Generate coverage comment with diff if base coverage is provided."""
    comment = generate_coverage_comment(coverage_data)
    
    if base_coverage is not None:
        totals = coverage_data.get('totals', {})
        covered_lines = totals.get('covered_lines', 0)
        num_statements = totals.get('num_statements', 0)
        
        if num_statements > 0:
            current_coverage = (covered_lines / num_statements) * 100
            diff = current_coverage - base_coverage
            
            if diff > 0:
                diff_emoji = "📈"
                diff_text = f"+{diff:.1f}%"
            elif diff < 0:
                diff_emoji = "📉"
                diff_text = f"{diff:.1f}%"
            else:
                diff_emoji = "➡️"
                diff_text = "±0.0%"
            
            # Insert diff info after the overall coverage line
            lines = comment.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('### 📊 Overall Coverage:'):
                    lines.insert(i + 1, f"- **Coverage Change**: {diff_emoji} {diff_text} (was {base_coverage:.1f}%)")
                    break
            
            comment = '\n'.join(lines)
    
    return comment


def main():
    """Main function."""
    coverage_data = load_coverage_data()
    if not coverage_data:
        # Generate a fallback comment when coverage data is not available
        fallback_comment = """## ⚠️ Coverage Report Unavailable

Coverage data could not be loaded. This may be due to:
- Coverage report not generated properly
- Missing coverage.json file
- Test execution failure

Please check the test logs for more information.

---
*This comment was automatically generated by the coverage analysis workflow.*
"""
        print(fallback_comment)
        with open('coverage_comment.md', 'w') as f:
            f.write(fallback_comment)
        print("⚠️ Fallback coverage comment generated", file=sys.stderr)
        return
    
    # Check if base coverage is provided (for PR diff)
    base_coverage = None
    if len(sys.argv) > 1:
        try:
            base_coverage = float(sys.argv[1])
        except ValueError:
            print("Warning: Invalid base coverage provided, ignoring", file=sys.stderr)
    
    # Generate comment
    if base_coverage is not None:
        comment = generate_coverage_diff_comment(coverage_data, base_coverage)
    else:
        comment = generate_coverage_comment(coverage_data)
    
    # Output comment to stdout for GitHub Actions
    print(comment)
    
    # Also save to file for debugging
    with open('coverage_comment.md', 'w') as f:
        f.write(comment)
    
    print("✅ Coverage comment generated successfully!", file=sys.stderr)


if __name__ == "__main__":
    main()