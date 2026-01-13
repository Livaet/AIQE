#!/bin/bash
# Build script for Linux/Mac

echo "================================================================================"
echo "Building MemoQ AIQE Connector Executable for Linux/Mac"
echo "================================================================================"
echo

echo "Checking for PyInstaller..."
if ! pip show pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

echo
echo "Building executable..."
echo

pyinstaller --name=memoq-aiqe-connector --onefile --console --clean \
  --hidden-import=anthropic \
  --hidden-import=openai \
  --hidden-import=zeep \
  --hidden-import=fastapi \
  --hidden-import=uvicorn \
  --hidden-import=yaml \
  --hidden-import=loguru \
  --hidden-import=pydantic \
  --hidden-import=requests \
  --hidden-import=aiohttp \
  --hidden-import=asyncio \
  --hidden-import=pandas \
  --add-data=config.yaml.example:. \
  --add-data=README.md:. \
  --add-data=AI_AGENT_RECOMMENDATION.md:. \
  main.py

echo
echo "============================================================================"
echo "Build complete!"
echo
echo "Executable location: dist/memoq-aiqe-connector"
echo
echo "Files to transfer to remote desktop:"
echo "  1. dist/memoq-aiqe-connector"
echo "  2. config.yaml (create from config.yaml.example)"
echo
echo "Make executable: chmod +x dist/memoq-aiqe-connector"
echo "Usage: ./memoq-aiqe-connector --help"
echo "============================================================================"
