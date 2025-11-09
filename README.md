# About

# Install

## Running from Source

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers** (required step):
   ```bash
   playwright install
   ```

   **Linux users**: If you get a "missing dependencies" warning, install system dependencies:
   ```bash
   playwright install-deps
   ```
   Or manually using apt:
   ```bash
   apt-get install libnspr4 libnss3 libgbm1 libasound2
   ```

3. Run PageHawk:
   ```bash
   python pagehawk.py -i <target> --ports <ports> -o <output_dir>
   ```

### Example Usage
```bash
python pagehawk.py -i localhost --ports 80,443,8080 -o example_outputs --subdir-screenshots --threads 10 -vvv
```

# Build

## Building a Standalone Executable

The `PageHawk_bundle.spec` file is **cross-platform** and works on Windows, Linux, and macOS. However, you must build on each target platform separately (a Windows build won't run on Linux, and vice versa).

### Prerequisites

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Make sure you have the Playwright browsers installed:
   ```bash
   playwright install
   ```

### Build Process

Run the following command to build the executable using the spec file:

```bash
pyinstaller --clean PageHawk_bundle.spec
```

### Platform-Specific Outputs

#### Windows
- **Output**: `dist\PageHawk.exe` (~150 MB)
- **Browser Path**: `%LOCALAPPDATA%\ms-playwright`
- **Icon**: Uses `pagehawk.ico`

#### Linux
- **Output**: `dist/PageHawk` (no extension, ~150 MB)
- **Browser Path**: `~/.cache/ms-playwright`
- **Icon**: None (Linux typically doesn't use .ico files)

#### macOS
- **Output**: `dist/PageHawk` (no extension, ~150 MB)
- **Browser Path**: `~/Library/Caches/ms-playwright`
- **Icon**: None

### What Gets Bundled
- Python runtime
- Playwright library
- Chromium headless browser
- FFmpeg
- All template files (HTML, CSS, JS)
- Logo and configuration files

### Testing the Executable

**Windows**:
```bash
dist\PageHawk.exe -i localhost --ports 80,443 -o test_output --subdir-screenshots -vvv
```

**Linux/macOS**:
```bash
./dist/PageHawk -i localhost --ports 80,443 -o test_output --subdir-screenshots -vvv
```

### Important Notes

- **Cross-compilation is not supported**: You must build on the target OS
- **The spec file is universal**: Same `PageHawk_bundle.spec` works on all platforms
- **Each binary is platform-specific**: Windows `.exe` won't run on Linux, and vice versa
- **Always use the spec file**: This ensures Playwright browsers are properly included