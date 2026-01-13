# Quick Start: Building Standalone Executable

This guide helps you quickly build a standalone executable for remote desktops without Python.

## ⚡ Fast Track (3 Steps)

### 1. Install Dependencies (on your local machine)

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 2. Build the Executable

**Windows:**
```cmd
build.bat
```

**Linux/Mac:**
```bash
chmod +x build.sh
./build.sh
```

Or use Python script:
```bash
python build_executable.py
```

### 3. Transfer to Remote Desktop

Copy these 2 files to your remote desktop:

1. **Executable:**
   - Windows: `dist/memoq-aiqe-connector.exe`
   - Linux: `dist/memoq-aiqe-connector`

2. **Config file:**
   - Copy `config.yaml.example` → `config.yaml`
   - Edit with your MemoQ and AI credentials

## 🚀 Using on Remote Desktop

### Windows
```cmd
memoq-aiqe-connector.exe --help
memoq-aiqe-connector.exe --project-guid YOUR-PROJECT-GUID --mode standalone
```

### Linux
```bash
chmod +x memoq-aiqe-connector
./memoq-aiqe-connector --help
./memoq-aiqe-connector --project-guid YOUR-PROJECT-GUID --mode standalone
```

## 📋 What You Need in config.yaml

Minimum required settings:

```yaml
memoq:
  server_url: "https://your-memoq-server.com:8081"
  username: "your-username"
  password: "your-password"

aiqe:
  ai_provider: "anthropic"  # or "openai"
  api_key: "your-ai-api-key-here"
  model: "claude-3-5-sonnet-20241022"  # or "gpt-4-turbo"
```

## ❓ Troubleshooting

**Build fails with "PyInstaller not found"**
```bash
pip install pyinstaller
```

**"config.yaml not found" on remote**
- Make sure config.yaml is in same folder as .exe
- Or specify: `--config C:\path\to\config.yaml`

**Antivirus blocks executable**
- Add exception for the .exe file
- Or build with: `pyinstaller --noupx ...`

**"SSL certificate verify failed"**
- Add to config.yaml:
  ```yaml
  memoq:
    verify_ssl: false
  ```

## 📖 Full Documentation

- Detailed build instructions: [BUILD.md](BUILD.md)
- Usage guide: [README.md](README.md)
- AI agent selection: [AI_AGENT_RECOMMENDATION.md](AI_AGENT_RECOMMENDATION.md)

## 💡 Tips

- **Executable size:** 50-100 MB is normal
- **Build time:** 2-5 minutes
- **Keep config.yaml secure:** It contains passwords/API keys
- **One executable per platform:** Build on Windows for Windows, Linux for Linux
