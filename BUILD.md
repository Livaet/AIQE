# Building Standalone Executable

This guide explains how to compile the MemoQ AIQE Connector into a standalone executable that can run on machines without Python installed.

## Prerequisites

On your **local machine** (where you'll build the executable):
- Python 3.8 or higher
- pip

## Step 1: Clone/Download the Repository

If you haven't already, get the code on your local machine:

```bash
git clone https://github.com/Livaet/AIQE.git
cd AIQE
git checkout claude/memoq-aiqe-connector-kkY5t
```

Or download the ZIP from GitHub and extract it.

## Step 2: Install Dependencies

On your local machine:

```bash
# Install regular dependencies
pip install -r requirements.txt

# Install PyInstaller for building executables
pip install pyinstaller
```

## Step 3: Build the Executable

### Option A: Using the Build Script (Recommended)

```bash
python build_executable.py
```

### Option B: Manual PyInstaller Command

**For Windows:**
```bash
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
  --add-data=config.yaml.example;. ^
  --add-data=README.md;. ^
  --add-data=AI_AGENT_RECOMMENDATION.md;. ^
  main.py
```

**For Linux/Mac:**
```bash
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
  --add-data=config.yaml.example:. \
  --add-data=README.md:. \
  --add-data=AI_AGENT_RECOMMENDATION.md:. \
  main.py
```

## Step 4: Locate the Executable

After building, you'll find:

```
dist/
  ├── memoq-aiqe-connector.exe   (Windows)
  └── memoq-aiqe-connector        (Linux/Mac)
```

The executable is typically 50-100 MB and includes everything needed to run.

## Step 5: Prepare Configuration File

Create your configuration file:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your actual credentials:
- MemoQ server URL and credentials
- AI provider API key (Anthropic or OpenAI)
- Quality thresholds
- Other settings

**IMPORTANT:** Keep `config.yaml` secure as it contains sensitive credentials!

## Step 6: Transfer to Remote Desktop

Copy these files to your remote desktop:

1. **The executable:**
   - `dist/memoq-aiqe-connector.exe` (Windows)
   - `dist/memoq-aiqe-connector` (Linux)

2. **Configuration file:**
   - `config.yaml` (with your credentials)

3. **Optional but recommended:**
   - `README.md`
   - `AI_AGENT_RECOMMENDATION.md`

### Transfer Methods:
- Remote Desktop copy/paste
- USB drive
- Network share
- SCP/SFTP
- Cloud storage (OneDrive, Dropbox, etc.)

## Step 7: Run on Remote Desktop

### Windows:
```cmd
cd C:\path\to\executable
memoq-aiqe-connector.exe --help
memoq-aiqe-connector.exe --project-guid YOUR-PROJECT-GUID --mode standalone
```

### Linux:
```bash
cd /path/to/executable
chmod +x memoq-aiqe-connector  # Make it executable
./memoq-aiqe-connector --help
./memoq-aiqe-connector --project-guid YOUR-PROJECT-GUID --mode standalone
```

## Usage Examples

### Check a specific project:
```bash
memoq-aiqe-connector.exe --project-guid abc-123-def-456 --mode standalone
```

### Check a specific document:
```bash
memoq-aiqe-connector.exe --project-guid abc-123 --document-guid xyz-789 --mode standalone
```

### Start API server:
```bash
memoq-aiqe-connector.exe --mode api --port 8080
```

### Use custom config file:
```bash
memoq-aiqe-connector.exe --config my-config.yaml --project-guid abc-123
```

## Directory Structure on Remote Desktop

Recommended setup:

```
C:\AIQE\  (or /opt/aiqe/ on Linux)
  ├── memoq-aiqe-connector.exe
  ├── config.yaml
  ├── logs\              (created automatically)
  ├── reports\           (created automatically)
  └── README.md
```

## Troubleshooting

### Build Issues

**"PyInstaller not found"**
```bash
pip install pyinstaller
```

**"Module not found" during build**
```bash
pip install -r requirements.txt
```

**Build takes a long time**
- Normal! Building can take 2-5 minutes
- PyInstaller analyzes all dependencies

**Executable is very large (100+ MB)**
- Normal! It includes Python interpreter and all libraries
- Use `--onefile` flag for single file (already in script)

### Runtime Issues on Remote Desktop

**"config.yaml not found"**
- Make sure `config.yaml` is in the same directory as the executable
- Or specify path: `--config /path/to/config.yaml`

**"Authentication failed"**
- Check MemoQ server URL in config.yaml
- Verify credentials are correct
- Ensure remote desktop can reach MemoQ server (network/firewall)

**"API key invalid"**
- Verify Anthropic or OpenAI API key in config.yaml
- Check for extra spaces or quotes

**Antivirus blocks executable**
- PyInstaller executables sometimes trigger false positives
- Add exception in antivirus software
- Or build with `--noupx` flag

**"SSL certificate verify failed"**
- If using self-signed MemoQ certificate, set in config.yaml:
  ```yaml
  memoq:
    verify_ssl: false
  ```

### Performance Issues

**Slow processing**
- Try faster AI model (e.g., Claude Haiku, GPT-4o)
- Reduce batch_size in config.yaml
- Check network latency to MemoQ server

**High memory usage**
- Normal for AI processing
- Executable may use 200-500 MB RAM
- Reduce batch_size if needed

## Platform-Specific Notes

### Windows
- Build on Windows machine for Windows executable
- May show console window (by design)
- Can run as scheduled task

### Linux
- Build on Linux for Linux executable
- Make executable: `chmod +x`
- Can run as systemd service

### macOS
- Build on Mac for macOS executable
- May need to allow in Security & Privacy settings
- Apple Silicon (M1/M2): build on ARM or use Rosetta

## Cross-Platform Building

To build for a different platform:

**Use Docker:**
```bash
# Build for Linux (on any platform)
docker build -t aiqe-builder .
docker run -v $(pwd)/dist:/app/dist aiqe-builder

# The executable will be in dist/
```

**Or use platform-specific VM:**
- Build Windows .exe on Windows VM
- Build Linux binary on Linux VM
- Build macOS binary on macOS machine

## Alternative: Use Directory Mode

If the single-file executable has issues, build as directory:

```bash
pyinstaller --onedir --console main.py
```

This creates `dist/main/` directory with:
- main.exe (smaller)
- DLL files and dependencies

Transfer the entire `dist/main/` directory to remote desktop.

## Security Considerations

1. **Protect config.yaml** - contains API keys and passwords
2. **Use environment variables** (optional):
   ```bash
   set MEMOQ_PASSWORD=your-password
   set ANTHROPIC_API_KEY=your-key
   ```
3. **Restrict file permissions** on config.yaml
4. **Don't commit** config.yaml to git (already in .gitignore)

## File Size Optimization

To reduce executable size:

```bash
# Use UPX compression (if available)
pyinstaller --onefile --console --upx-dir=/path/to/upx main.py

# Or exclude unused modules
pyinstaller --onefile --console \
  --exclude-module matplotlib \
  --exclude-module PIL \
  main.py
```

## Automated Builds

For CI/CD, use GitHub Actions:

```yaml
# .github/workflows/build.yml
name: Build Executable
on: [push]
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pip install pyinstaller
      - run: python build_executable.py
      - uses: actions/upload-artifact@v2
        with:
          name: memoq-aiqe-connector
          path: dist/
```

## Support

If you encounter issues:
1. Check this BUILD.md file
2. Review error messages carefully
3. Check PyInstaller documentation: https://pyinstaller.org
4. Open issue on GitHub

## License

The executable contains the same MIT License as the source code.
