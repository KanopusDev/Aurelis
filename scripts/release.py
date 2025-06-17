#!/usr/bin/env python3
"""
Release script for Aurelis.
This script automates the release process by:
1. Checking that the working directory is clean
2. Updating the version number (patch, minor, or major)
3. Updating the changelog
4. Creating a git tag and commit
5. Pushing to GitHub

Usage:
    python scripts/release.py [patch|minor|major]

Requirements:
    - Git command-line tool
    - Poetry
    - GitHub CLI (optional, for creating GitHub releases)
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Validate in correct directory
if not os.path.exists("aurelis") or not os.path.exists("pyproject.toml"):
    sys.exit("Error: Please run this script from the project root directory")

def run_command(cmd, check=True):
    """Run a shell command and return its output."""
    return subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)

def check_git_clean():
    """Check if the git working directory is clean."""
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        sys.exit("Error: Git working directory is not clean. Please commit or stash changes first.")
    
    print("✓ Git working directory is clean")

def get_current_version():
    """Get current version from pyproject.toml."""
    result = run_command("poetry version --short")
    return result.stdout.strip()

def bump_version(level):
    """Bump the version according to the specified level."""
    if level not in ["patch", "minor", "major"]:
        sys.exit(f"Error: Invalid version level '{level}'. Use 'patch', 'minor', or 'major'")

    current_version = get_current_version()
    result = run_command(f"poetry version {level}")
    new_version = get_current_version()
    
    print(f"✓ Bumped version from {current_version} to {new_version} ({level})")
    return new_version

def update_changelog(version):
    """Update CHANGELOG.md with new version."""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        with open(changelog_path, "w") as f:
            f.write("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n")
    
    with open(changelog_path, "r") as f:
        content = f.read()

    today = datetime.now().strftime("%Y-%m-%d")
    new_section = f"## [{version}] - {today}\n\n### Added\n- \n\n### Changed\n- \n\n### Fixed\n- \n\n"
    
    # Find the position to insert the new section (after the header)
    header_match = re.search(r"# Changelog.*?\n\n", content, re.DOTALL)
    if header_match:
        insert_position = header_match.end()
        new_content = content[:insert_position] + new_section + content[insert_position:]
        with open(changelog_path, "w") as f:
            f.write(new_content)
        print(f"✓ Updated CHANGELOG.md with version {version}")
        print("  Please edit the changelog to add release notes")
        return True
    
    print("⚠ Could not update CHANGELOG.md automatically")
    return False

def create_git_tag(version):
    """Create a git tag and commit for the new version."""
    run_command(f'git add pyproject.toml CHANGELOG.md')
    run_command(f'git commit -m "Release version {version}"')
    run_command(f'git tag -a v{version} -m "Version {version}"')
    print(f"✓ Created git commit and tag v{version}")

def push_to_github():
    """Push changes and tags to GitHub."""
    confirm = input("Do you want to push changes to GitHub? (y/n): ")
    if confirm.lower() != 'y':
        print("Skipping push to GitHub")
        return
    
    run_command("git push")
    run_command("git push --tags")
    print("✓ Pushed changes and tags to GitHub")

def create_github_release(version):
    """Create a GitHub release (requires GitHub CLI)."""
    has_gh = run_command("which gh", check=False)
    if has_gh.returncode != 0:
        print("⚠ GitHub CLI not found, skipping release creation")
        print("  To create a release manually, go to:")
        print("  https://github.com/kanopusdev/aurelis/releases/new?tag=v" + version)
        return
    
    confirm = input("Do you want to create a GitHub release? (y/n): ")
    if confirm.lower() != 'y':
        print("Skipping GitHub release creation")
        print("  To create a release manually, go to:")
        print("  https://github.com/kanopusdev/aurelis/releases/new?tag=v" + version)
        return
    
    print("Creating GitHub release...")
    print("Opening editor for release notes...")
    run_command(f'gh release create v{version} --title "Aurelis {version}" --notes-file -')

def main():
    parser = argparse.ArgumentParser(description="Aurelis release script")
    parser.add_argument("level", choices=["patch", "minor", "major"], 
                        help="Version level to bump")
    parser.add_argument("--skip-checks", action="store_true", 
                        help="Skip git clean checks")
    
    args = parser.parse_args()
    
    print("=== Aurelis Release Process ===")
    
    if not args.skip_checks:
        check_git_clean()
    
    # Bump version
    new_version = bump_version(args.level)
    
    # Update changelog
    update_changelog(new_version)
    
    # Pause for manual changelog edit
    input("Press Enter after updating the CHANGELOG.md...")
    
    # Create git tag and commit
    create_git_tag(new_version)
    
    # Push to GitHub
    push_to_github()
    
    # Create GitHub release
    create_github_release(new_version)
    
    print(f"\n✅ Release {new_version} completed!")
    print(f"PyPI package will be published automatically when the GitHub release is created.")
    print(f"You can also manually trigger the workflow from the GitHub Actions tab.")

if __name__ == "__main__":
    main()
