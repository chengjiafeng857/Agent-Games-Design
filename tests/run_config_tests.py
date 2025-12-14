#!/usr/bin/env python3
"""
Test runner for configuration system tests.

This script runs the configuration tests and provides a summary of results.

Usage:
    python tests/run_config_tests.py
    # or
    uv run python tests/run_config_tests.py
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run configuration tests."""
    print("=" * 70)
    print("🧪 Running Configuration System Tests")
    print("=" * 70)
    print()
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    test_file = project_root / "tests" / "test_configuration.py"
    
    if not test_file.exists():
        print(f"❌ Error: Test file not found at {test_file}")
        return 1
    
    print(f"📁 Project root: {project_root}")
    print(f"📝 Test file: {test_file}")
    print()
    
    # Run pytest with verbose output
    try:
        print("🚀 Running tests with pytest...")
        print("-" * 70)
        
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(test_file),
                "-v",
                "--tb=short",
                "--color=yes",
            ],
            cwd=str(project_root),
            capture_output=False,
        )
        
        print()
        print("=" * 70)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print(f"❌ Tests failed with exit code {result.returncode}")
        
        print("=" * 70)
        
        return result.returncode
        
    except FileNotFoundError:
        print()
        print("=" * 70)
        print("❌ Error: pytest not found!")
        print()
        print("Please install pytest:")
        print("  uv sync --extra dev")
        print()
        print("Or install manually:")
        print("  pip install pytest pytest-asyncio")
        print("=" * 70)
        return 1
    
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Error running tests: {e}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

