#!/usr/bin/env python
"""
Test runner for kev-graph-rag project.
Run this script using: uv run python run_tests.py [options]
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run tests for kev-graph-rag project")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only (requires valid .env)")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--module", type=str, default="", help="Test specific module, e.g. 'utils.document_parser'")
    
    args = parser.parse_args()
    
    # Default to unit tests if nothing specified
    if not (args.unit or args.integration or args.all or args.module):
        print("No test type specified. Defaulting to unit tests.")
        args.unit = True
        
    # Build pytest command
    cmd = ["pytest", "-v"]
    
    # Add markers based on test type
    if args.unit:
        cmd.append("-m")
        cmd.append("unit")
    elif args.integration:
        cmd.append("-m")
        cmd.append("integration")
    # For --all, no specific marker needed
    
    # Add coverage options if requested
    if args.coverage:
        cmd.extend(["--cov=utils", "--cov-report=term", "--cov-report=html:coverage_report"])
        
    # Add specific module if requested
    if args.module:
        module_path = args.module.replace(".", "/")
        if not module_path.startswith("tests/") and "test_" not in module_path:
            # Convert module path to test path if needed
            if module_path.startswith("utils/"):
                module_path = f"tests/{module_path}"
            else:
                module_path = f"tests/utils/{module_path}"
        
        # Ensure we're looking at test_* files
        if not Path(module_path).exists() and "test_" not in module_path:
            module_parts = Path(module_path).parts
            module_path = str(Path(*module_parts[:-1]) / f"test_{module_parts[-1]}")
        
        cmd.append(module_path)
        
    # Print command for transparency
    cmd_str = " ".join(cmd)
    print(f"Running: {cmd_str}")
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print("\nTests completed successfully!")
            
            # Show coverage report location
            if args.coverage:
                coverage_path = Path.cwd() / "coverage_report" / "index.html"
                print(f"Coverage report generated: {coverage_path}")
                
            return 0
        else:
            print(f"\nTests failed with exit code {result.returncode}")
            return result.returncode
            
    except subprocess.CalledProcessError as e:
        print(f"\nError running tests: {e}")
        return e.returncode
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
