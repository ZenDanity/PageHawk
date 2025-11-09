# About

**PageHawk** is a web reconnaissance tool that automatically visits and screenshots web services across multiple targets and ports. It supports IP addresses, URLs, domains, CIDR ranges, and Nmap XML output files as input.

## Features
- **Multiple input formats**: IP addresses, URLs, domains, CIDR ranges, Nmap XML files, or text files
- **Automatic protocol detection**: Tries both HTTP and HTTPS for each target:port combination
- **Multithreaded scanning**: Configurable concurrent threads for fast scanning (default: 10 threads)
- **Headless browser automation**: Uses Playwright Chromium for accurate screenshots
- **HTML report generation**: Interactive, standalone HTML report with embedded screenshots
- **Status indicators**: Visual indicators for successful (green) and failed (red) connections
- **Modal image viewer**: Click thumbnails to view full-size screenshots
- **Execution timer**: Displays total scan duration
- **Cross-platform**: Runs on Windows, Linux, and macOS

# Use

## Use From Release / Binary

Just download the appropriate release file for Windows or Linux and run it.

## Use From Source
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

## Example Usage

### Basic scan with default ports (80, 443, 8080, 8443)
```bash
python pagehawk.py -i 192.168.1.1 -o output_dir
```

### Scan multiple IPs with custom ports
```bash
python pagehawk.py -i 192.168.1.1,192.168.1.2,10.0.0.5 --ports 80,443,8000,8443 -o results
```

### Scan a CIDR range
```bash
python pagehawk.py -i 192.168.1.0/24 --ports 80,443 -o network_scan
```

### Scan from Nmap XML output
```bash
python pagehawk.py -i nmap_scan.xml -o nmap_results
```

### Scan URLs with paths
```bash
python pagehawk.py -i example.com/admin,example.com/login --ports 80,443 -o admin_pages
```

### Advanced options with threading and verbose output
```bash
python pagehawk.py -i targets.txt --ports 80,443,8080 -o example_outputs --subdir-screenshots --threads 20 -vvv
```

### Full example with all options
```bash
python pagehawk.py \
  -i 192.168.1.0/24 \
  --ports 80,443,8080,8443 \
  -o detailed_scan \
  --subdir-screenshots \
  --subdir-timestamped \
  --threads 15 \
  --delay-from 100 \
  --delay-to 500 \
  -vvv
```

### Command-line Options
- `-i, --input`: Target(s) - IP, URL, domain, CIDR, Nmap XML, or text file
- `-o, --output`: Output directory for results
- `--ports`: Comma-separated list of ports (default: 80,443,8080,8443)
- `--threads`: Number of concurrent threads (default: 10)
- `--subdir-screenshots`: Store screenshots in subdirectory
- `--subdir-timestamped`: Create timestamped output subdirectory
- `--delay-from`, `--delay-to`: Random delay range in milliseconds
- `--proxy-*`: Proxy configuration options
- `-v, -vv, -vvv`: Verbosity levels (info, debug, extra debug)

# Install

## Install From Release / Binary

No need to "install", just download the appropriate release file for Windows or Linux and run it.

## Install From Source

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation Steps

1. Clone or download the repository:
   ```bash
   git clone <repository-url>
   cd pagehawk
   ```

2. (Optional but recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers** (required step):
   ```bash
   playwright install
   ```

5. **Linux users only**: If you get a "missing dependencies" warning, install system dependencies:
   ```bash
   playwright install-deps
   ```
   
   Or manually using apt (if `playwright install-deps` doesn't work):
   ```bash
   apt-get install libnspr4 libnss3 libgbm1 libasound2t64
   ```
   
   **Note for Kali Linux users**: You may need to install additional packages:
   ```bash
   apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
     libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
     libxrandr2 libgbm1 libasound2t64 libpango-1.0-0 libcairo2 \
     libatspi2.0-0 libgdk-pixbuf-2.0-0 fonts-liberation fonts-unifont
   ```

6. Verify installation by running PageHawk:
   ```bash
   python pagehawk.py -h
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
