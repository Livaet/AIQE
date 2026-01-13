# Complete Guide: From GitHub to Executable

This guide walks you through everything from downloading the code to running the executable on your remote desktop.

## Prerequisites

**On your local machine, you need:**
- Windows, Mac, or Linux computer
- Python 3.8 or higher ([download here](https://www.python.org/downloads/))
- Internet connection

**You DON'T need Python on your remote desktop** - that's the whole point!

---

## Step 1: Get the Code on Your Local Machine

You have 2 options:

### Option A: Download ZIP (Easiest - No Git Required)

1. **Go to GitHub:**
   - Open browser and go to: https://github.com/Livaet/AIQE

2. **Switch to the correct branch:**
   - Click the branch dropdown (says "main" by default)
   - Select: `claude/memoq-aiqe-connector-kkY5t`

3. **Download:**
   - Click the green "Code" button
   - Click "Download ZIP"
   - Save to your computer (e.g., `Downloads/AIQE-claude-memoq-aiqe-connector-kkY5t.zip`)

4. **Extract:**
   - Right-click the ZIP file → "Extract All"
   - Choose a location (e.g., `C:\Projects\AIQE` or `~/Projects/AIQE`)
   - Click "Extract"

5. **Open Terminal/Command Prompt in that folder:**
   - **Windows:** Hold Shift, right-click in the folder → "Open PowerShell window here" or "Open Command Prompt here"
   - **Mac:** Right-click folder → "New Terminal at Folder"
   - **Linux:** Right-click → "Open Terminal Here"

### Option B: Use Git (If You Have It)

1. **Open Terminal/Command Prompt**

2. **Clone the repository:**
   ```bash
   cd C:\Projects  # or cd ~/Projects on Mac/Linux
   git clone https://github.com/Livaet/AIQE.git
   cd AIQE
   git checkout claude/memoq-aiqe-connector-kkY5t
   ```

---

## Step 2: Verify Python is Installed

In your terminal/command prompt, run:

```bash
python --version
```

Should show: `Python 3.8.x` or higher

**If it says "python not found":**
- Try: `python3 --version`
- Or download Python from: https://www.python.org/downloads/
- **Important:** When installing, check "Add Python to PATH"

---

## Step 3: Install Dependencies

In the terminal (still in the AIQE folder):

```bash
pip install -r requirements.txt
```

This installs all the libraries needed (takes 1-2 minutes).

**If you get "pip not found":**
- Try: `python -m pip install -r requirements.txt`
- Or: `python3 -m pip install -r requirements.txt`

Then install PyInstaller:

```bash
pip install pyinstaller
```

---

## Step 4: Build the Executable

Now run the build script:

### Windows (Command Prompt or PowerShell):
```cmd
build.bat
```

### Mac/Linux (Terminal):
```bash
chmod +x build.sh
./build.sh
```

### Alternative (works on all platforms):
```bash
python build_executable.py
```

**This will take 2-5 minutes.** You'll see lots of output - that's normal!

When done, you'll see:
```
✓ Build successful!
Executable location: dist/memoq-aiqe-connector.exe
```

---

## Step 5: Prepare Configuration File

1. **Copy the example config:**
   ```bash
   # Windows
   copy config.yaml.example config.yaml

   # Mac/Linux
   cp config.yaml.example config.yaml
   ```

2. **Edit config.yaml** (use Notepad, VS Code, or any text editor):

   Find and update these sections:

   ```yaml
   memoq:
     server_url: "https://your-memoq-server.com:8081"
     username: "your-memoq-username"
     password: "your-memoq-password"

   aiqe:
     ai_provider: "anthropic"  # Use "openai" if you have OpenAI
     api_key: "sk-ant-your-anthropic-api-key"  # Your actual API key
     model: "claude-3-5-sonnet-20241022"
   ```

3. **Save** the file

**⚠️ IMPORTANT:** This file contains passwords! Keep it secure!

---

## Step 6: Find Your Built Files

Navigate to the `dist` folder:

```bash
cd dist
```

You should see:

**Windows:**
- `memoq-aiqe-connector.exe` (50-100 MB)

**Mac/Linux:**
- `memoq-aiqe-connector` (50-100 MB)

---

## Step 7: Transfer to Remote Desktop

You need to copy 2 files to your remote desktop:

1. **The executable:**
   - Windows: `dist\memoq-aiqe-connector.exe`
   - Linux: `dist/memoq-aiqe-connector`

2. **The config file:**
   - `config.yaml` (the one you edited with your credentials)

### Transfer Methods:

#### Method 1: Remote Desktop Copy/Paste
1. Connect to remote desktop
2. On local machine: Right-click the files → Copy
3. On remote desktop: Right-click → Paste

#### Method 2: USB Drive
1. Copy both files to USB drive
2. Plug into remote desktop
3. Copy from USB to remote desktop (e.g., `C:\AIQE\`)

#### Method 3: Network Share
1. Place files in shared network folder
2. Access from remote desktop
3. Copy to local drive on remote desktop

#### Method 4: Cloud Storage (OneDrive, Dropbox, Google Drive)
1. Upload files to cloud
2. Download on remote desktop
3. **Remember to delete from cloud after** (contains passwords!)

---

## Step 8: Run on Remote Desktop

On your **remote desktop** (no Python needed):

### First Time Setup:

1. **Create a folder:**
   ```cmd
   # Windows
   mkdir C:\AIQE
   cd C:\AIQE

   # Linux
   mkdir ~/aiqe
   cd ~/aiqe
   ```

2. **Copy your 2 files there:**
   - `memoq-aiqe-connector.exe` (or just `memoq-aiqe-connector` on Linux)
   - `config.yaml`

3. **On Linux, make it executable:**
   ```bash
   chmod +x memoq-aiqe-connector
   ```

### Test It:

```cmd
# Windows
memoq-aiqe-connector.exe --help

# Linux
./memoq-aiqe-connector --help
```

You should see the help menu!

---

## Step 9: Use It!

### Check a Project:

```cmd
# Windows
memoq-aiqe-connector.exe --project-guid YOUR-PROJECT-GUID-HERE --mode standalone

# Linux
./memoq-aiqe-connector --project-guid YOUR-PROJECT-GUID-HERE --mode standalone
```

### Check a Specific Document:

```cmd
# Windows
memoq-aiqe-connector.exe --project-guid PROJECT-GUID --document-guid DOCUMENT-GUID --mode standalone

# Linux
./memoq-aiqe-connector --project-guid PROJECT-GUID --document-guid DOCUMENT-GUID --mode standalone
```

### Start API Server:

```cmd
# Windows
memoq-aiqe-connector.exe --mode api --port 8080

# Linux
./memoq-aiqe-connector --mode api --port 8080
```

---

## Complete Example Walkthrough

Here's a complete example from start to finish:

```powershell
# === ON YOUR LOCAL MACHINE ===

# 1. Download and extract (if using ZIP method)
# [Extract AIQE-claude-memoq-aiqe-connector-kkY5t.zip to C:\Projects\AIQE]

# 2. Open PowerShell in that folder
cd C:\Projects\AIQE

# 3. Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# 4. Build
.\build.bat

# Wait 2-5 minutes...

# 5. Create config
copy config.yaml.example config.yaml
notepad config.yaml
# [Edit and save]

# 6. Files are ready!
# - dist\memoq-aiqe-connector.exe
# - config.yaml

# === TRANSFER TO REMOTE DESKTOP ===
# [Copy those 2 files via RDP, USB, or cloud]

# === ON REMOTE DESKTOP ===

# 7. Put files in a folder
mkdir C:\AIQE
cd C:\AIQE
# [Paste memoq-aiqe-connector.exe and config.yaml here]

# 8. Test
.\memoq-aiqe-connector.exe --help

# 9. Run quality check
.\memoq-aiqe-connector.exe --project-guid abc-123-def-456 --mode standalone
```

---

## Troubleshooting

### On Local Machine (During Build)

**"python not found"**
- Install Python from python.org
- Check "Add to PATH" during installation
- Restart terminal/command prompt

**"pip not found"**
- Try: `python -m pip install ...`
- Or reinstall Python with "Add to PATH"

**"PyInstaller not found"**
```bash
pip install pyinstaller
```

**Build fails with errors**
- Make sure you're in the AIQE folder
- Try: `pip install --upgrade -r requirements.txt`
- Check internet connection

**Build takes forever**
- Normal! Can take 5 minutes
- Don't interrupt it

### On Remote Desktop (During Use)

**"config.yaml not found"**
- Make sure config.yaml is in same folder as .exe
- Or specify full path: `--config C:\full\path\to\config.yaml`

**"Authentication failed"**
- Check MemoQ credentials in config.yaml
- Verify server URL is correct
- Test network access to MemoQ server

**"Invalid API key"**
- Check Anthropic/OpenAI API key in config.yaml
- Make sure there are no extra spaces or quotes
- Verify key is active (check your Anthropic/OpenAI dashboard)

**Antivirus blocks the .exe**
- Windows Defender sometimes flags PyInstaller executables
- Right-click .exe → Properties → Unblock
- Or add to antivirus exceptions

**"SSL certificate verify failed"**
- If using self-signed MemoQ certificate, add to config.yaml:
  ```yaml
  memoq:
    verify_ssl: false
  ```

---

## Where to Get API Keys

### Anthropic (Claude) - Recommended
1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys"
4. Create new key
5. Copy the key (starts with `sk-ant-...`)
6. Paste into config.yaml under `aiqe.api_key`

### OpenAI (GPT) - Alternative
1. Go to: https://platform.openai.com/
2. Sign up or log in
3. Go to "API Keys"
4. Create new key
5. Copy the key (starts with `sk-...`)
6. Paste into config.yaml under `aiqe.api_key`
7. Change `aiqe.ai_provider` to `"openai"`
8. Change `aiqe.model` to `"gpt-4-turbo"`

---

## File Structure Reference

### On Your Local Machine:
```
C:\Projects\AIQE\          (or ~/Projects/AIQE)
├── main.py
├── requirements.txt
├── build.bat              ← Run this to build
├── build.sh
├── config.yaml.example
├── config.yaml           ← Your credentials
├── src\
│   ├── __init__.py
│   ├── memoq_client.py
│   ├── aiqe_engine.py
│   └── ...
└── dist\                 ← Build output folder
    └── memoq-aiqe-connector.exe  ← The executable!
```

### On Remote Desktop:
```
C:\AIQE\                   (or ~/aiqe)
├── memoq-aiqe-connector.exe  ← Copy this
├── config.yaml               ← Copy this
├── logs\                     ← Created automatically
└── reports\                  ← Created automatically
```

---

## Quick Reference Commands

### Local Machine (Building):
```bash
pip install -r requirements.txt
pip install pyinstaller
build.bat              # Windows
./build.sh             # Mac/Linux
```

### Remote Desktop (Using):
```cmd
# Test
memoq-aiqe-connector.exe --help

# Check project
memoq-aiqe-connector.exe --project-guid XXX --mode standalone

# Check document
memoq-aiqe-connector.exe --project-guid XXX --document-guid YYY --mode standalone

# API mode
memoq-aiqe-connector.exe --mode api --port 8080
```

---

## Need Help?

1. Read this file again carefully
2. Check the error message
3. See [BUILD.md](BUILD.md) for detailed troubleshooting
4. See [README.md](README.md) for usage documentation
5. Open an issue on GitHub

---

## Success Checklist

✅ Python installed on local machine
✅ Code downloaded from GitHub
✅ Dependencies installed (`pip install -r requirements.txt`)
✅ PyInstaller installed (`pip install pyinstaller`)
✅ Executable built (ran `build.bat` or `build.sh`)
✅ config.yaml created and edited with credentials
✅ Both files transferred to remote desktop
✅ Tested with `--help` command
✅ Successfully ran quality check

If all checked, you're good to go! 🎉
