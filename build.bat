@echo off
REM Build script for Windows
echo ================================================================================
echo Building MemoQ AIQE Connector Executable for Windows
echo ================================================================================
echo.

echo Checking for PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Building executable...
echo.

pyinstaller --name=memoq-aiqe-connector --onefile --console --clean ^
  --hidden-import=anthropic ^
  --hidden-import=openai ^
  --hidden-import=zeep ^
  --hidden-import=fastapi ^
  --hidden-import=uvicorn ^
  --hidden-import=yaml ^
  --hidden-import=loguru ^
  --hidden-import=pydantic ^
  --hidden-import=requests ^
  --hidden-import=aiohttp ^
  --hidden-import=asyncio ^
  --hidden-import=pandas ^
  --add-data=config.yaml.example;. ^
  --add-data=README.md;. ^
  --add-data=AI_AGENT_RECOMMENDATION.md;. ^
  main.py

echo.
echo ============================================================================
echo Build complete!
echo.
echo Executable location: dist\memoq-aiqe-connector.exe
echo.
echo Files to transfer to remote desktop:
echo   1. dist\memoq-aiqe-connector.exe
echo   2. config.yaml (create from config.yaml.example)
echo.
echo Usage: memoq-aiqe-connector.exe --help
