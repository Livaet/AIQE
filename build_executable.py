#!/usr/bin/env python3
"""
Build script for creating standalone executable
"""

import os
import sys
import subprocess

def build_executable():
    """Build standalone executable using PyInstaller"""

    print("Building MemoQ AIQE Connector executable...")
    print("=" * 80)

    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=memoq-aiqe-connector',
        '--onefile',  # Single executable file
        '--console',  # Console application
        '--clean',

        # Include all source modules
        '--hidden-import=anthropic',
        '--hidden-import=openai',
        '--hidden-import=zeep',
        '--hidden-import=fastapi',
        '--hidden-import=uvicorn',
        '--hidden-import=yaml',
        '--hidden-import=loguru',
        '--hidden-import=pydantic',
        '--hidden-import=requests',

        # Add data files
        '--add-data=config.yaml.example:.',
        '--add-data=README.md:.',
        '--add-data=AI_AGENT_RECOMMENDATION.md:.',

        # Main entry point
        'main.py'
    ]

    # Adjust data file separator for Windows
    if sys.platform == 'win32':
        cmd = [arg.replace(':', ';') if '--add-data' in arg else arg for arg in cmd]

    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 80)
        print("✓ Build successful!")
        print("\nExecutable location:")
        print(f"  - dist/memoq-aiqe-connector.exe (Windows)")
        print(f"  - dist/memoq-aiqe-connector (Linux/Mac)")
        print("\nFiles to transfer to remote desktop:")
        print("  1. dist/memoq-aiqe-connector[.exe]")
        print("  2. config.yaml (create from config.yaml.example)")
        print("\nUsage on remote desktop:")
        print("  ./memoq-aiqe-connector --help")
        print("=" * 80)
    else:
        print("\n✗ Build failed!")
        sys.exit(1)

if __name__ == '__main__':
    build_executable()
