# Installation Guide

Complete step-by-step installation guide for the Vietnamese Food Detection system.

---

## Table of Contents
- [System Requirements](#system-requirements)
- [Windows Installation](#windows-installation)
- [macOS Installation](#macos-installation)
- [Linux Installation](#linux-installation)
- [GPU Setup (Optional)](#gpu-setup-optional)
- [Troubleshooting](#troubleshooting)
- [Verification](#verification)

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 7+, macOS 10.12+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **RAM**: 4GB (8GB recommended)
- **Disk Space**: 2GB free (for model and dataset)
- **Camera**: Webcam or external USB camera

### Recommended Requirements
- **OS**: Windows 10/11, macOS 11+, or Ubuntu 20.04+
- **Python**: 3.10 or 3.11
- **RAM**: 8GB+ (for smooth operation)
- **Disk Space**: 5GB+ (for full dataset)
- **GPU**: NVIDIA GPU with CUDA 11.8+ (for fast inference)
- **Camera**: USB 3.0+ camera (30 FPS)

### GPU Support (Optional)
- **NVIDIA**: CUDA 11.8+, cuDNN 8.0+
- **AMD**: Not officially supported (CPU fallback)
- **Intel**: Integrated graphics (CPU fallback)

---

## Windows Installation

### Step 1: Install Python

#### Option A: Official Python
1. Visit https://www.python.org/downloads/
2. Download Python 3.10 or 3.11
3. Run installer
4. **Important**: Check "Add Python to PATH"
5. Complete installation

#### Option B: Anaconda (Recommended for Windows)
1. Download from https://www.anaconda.com/download
2. Run installer
3. Follow installation wizard
4. Verify installation:
   ```bash
   python --version
   ```

### Step 2: Clone or Download Project

#### Option A: Using Git
```bash
# Install Git if not already installed
# Visit: https://git-scm.com/download/win

git clone https://github.com/yourusername/food_detection.git
cd food_selected_pho_bun
```

#### Option B: Download ZIP
1. Go to GitHub repository
2. Click "Code" → "Download ZIP"
3. Extract ZIP file
4. Open Command Prompt in extracted folder

### Step 3: Create Virtual Environment

```bash
# Open Command Prompt or PowerShell
cd path\to\food_selected_pho_bun

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify activation (should show (venv) in prompt)
```

### Step 4: Install Dependencies

```bash
# Make sure venv is activated
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 5: Configure Model Path

1. Open `app/config.py` in text editor
2. Find line with `MODEL_PATH`
3. Update to your model location:
   ```python
   MODEL_PATH = r"C:\Users\YourUsername\Downloads\food_selected_pho_bun\food_detection_36class_1100\food_detection_36class_1100_resume\yolov8s_vietfood_36class_1100\weights\best.pt"
   ```

### Step 6: Test Installation

```bash
# Navigate to app folder
cd app

# Run the application
python main.py
```

---

## macOS Installation

### Step 1: Install Python

#### Option A: Homebrew (Recommended)
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.10

# Verify
python3 --version
```

#### Option B: Official Python
1. Visit https://www.python.org/downloads/macos/
2. Download macOS installer for Python 3.10+
3. Run installer
4. Follow wizard

### Step 2: Clone Project

```bash
# Using Git
git clone https://github.com/yourusername/food_detection.git
cd food_selected_pho_bun

# Or download and extract ZIP file
```

### Step 3: Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Verify (should show (venv) in prompt)
```

### Step 4: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify
pip list
```

### Step 5: Configure Model Path

```bash
# Edit config file
nano app/config.py

# Find and update MODEL_PATH:
# MODEL_PATH = r"/Users/YourUsername/path/to/best.pt"
```

### Step 6: Grant Camera Permissions

1. Go to System Preferences → Security & Privacy
2. Select "Camera"
3. Add Terminal to allowed apps
4. Restart Terminal

### Step 7: Test

```bash
cd app
python main.py
```

---

## Linux Installation

### Step 1: Install Python & Dependencies

#### Ubuntu/Debian
```bash
# Update package manager
sudo apt update
sudo apt upgrade

# Install Python and pip
sudo apt install python3.10 python3-pip python3-venv

# Install system dependencies for OpenCV
sudo apt install libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1

# Verify
python3 --version
pip3 --version
```

#### Fedora/RHEL
```bash
# Install Python
sudo dnf install python3 python3-pip

# Install dependencies
sudo dnf install mesa-libGL glib2 libSM libxrender

# Verify
python3 --version
```

### Step 2: Clone Project

```bash
git clone https://github.com/yourusername/food_detection.git
cd food_selected_pho_bun
```

### Step 3: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure Model Path

```bash
nano app/config.py

# Update MODEL_PATH:
# MODEL_PATH = r"/home/username/path/to/best.pt"
```

### Step 6: Test Installation

```bash
cd app
python main.py
```

---

## GPU Setup (Optional)

### For NVIDIA GPU

#### Step 1: Install CUDA
```bash
# Visit: https://developer.nvidia.com/cuda-downloads
# Download CUDA Toolkit 11.8+
# Follow installation instructions for your OS
```

#### Step 2: Install cuDNN
```bash
# Visit: https://developer.nvidia.com/cudnn
# Download cuDNN 8.0+
# Extract and copy files to CUDA installation directory
```

#### Step 3: Install PyTorch with GPU Support
```bash
# Activate virtual environment
# Visit: https://pytorch.org/
# Select appropriate configuration

# Example for CUDA 11.8:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Step 4: Verify GPU
```bash
python -c "import torch; print(torch.cuda.is_available())"
# Should print: True
```

### For macOS with M1/M2

```bash
# macOS uses CPU (Metal support in progress)
# Install native PyTorch for Apple Silicon
pip install torch torchvision torchaudio
```

---

## Troubleshooting

### Python Not Found
**Problem**: `'python' is not recognized as an internal or external command`

**Solution**:
- Windows: Reinstall Python and check "Add Python to PATH"
- macOS/Linux: Use `python3` instead of `python`

### Virtual Environment Issues

**Problem**: Can't activate virtual environment

**Solution**:
```bash
# Windows
# Check Scripts folder exists
dir venv\Scripts

# Try full path
venv\Scripts\python.exe -m pip list

# macOS/Linux
ls venv/bin
source venv/bin/activate
```

### Module Not Found
**Problem**: `ModuleNotFoundError: No module named 'cv2'`

**Solution**:
```bash
# Ensure virtual environment is activated
which python  # macOS/Linux
where python  # Windows

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Camera Not Working
**Problem**: Camera doesn't initialize in application

**Solution**:
```bash
# Windows: Check Device Manager
# - Plug/unplug camera
# - Update camera drivers

# macOS: Grant permissions
# System Preferences → Security & Privacy → Camera

# Linux: Check camera device
ls /dev/video*
sudo usermod -a -G video $USER
```

### Low FPS or Slow Detection
**Problem**: Detection is very slow

**Solution**:
1. Reduce image size in `config.py`:
   ```python
   CAMERA_WIDTH = 640
   CAMERA_HEIGHT = 480
   ```

2. Use GPU (if available)

3. Reduce confidence score adjustment slider

4. Close other applications

### Model File Not Found
**Problem**: `FileNotFoundError: [Errno 2] No such file or directory`

**Solution**:
1. Check `MODEL_PATH` in `config.py`
2. Verify file exists:
   ```bash
   # Windows
   dir "C:\path\to\best.pt"
   
   # macOS/Linux
   ls /path/to/best.pt
   ```
3. Use absolute path, not relative

### Out of Memory
**Problem**: Application crashes with memory error

**Solution**:
```python
# Edit config.py
CAMERA_WIDTH = 640   # Reduce from 1280
CAMERA_HEIGHT = 480  # Reduce from 720

# Use CPU instead of GPU
# Remove GPU device from code
```

---

## ✅ Verification

### Check Installation

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Check Python version
python --version
# Should be 3.8+

# Check installed packages
pip list
# Should show: opencv-python, Pillow, ultralytics, etc.

# Test imports
python -c "import cv2, PIL, ultralytics; print('All imports OK!')"
```

### Test Application

```bash
# Navigate to app folder
cd app

# Run application
python main.py

# Verify:
# 1. Window opens without errors
# 2. Camera initializes
# 3. Model loads (check console output)
# 4. Detection starts when clicking "Start Detection"
```

### Quick Test

```python
# Create test script: test_installation.py
from ultralytics import YOLO
import cv2

print("Testing installation...")

# Test PyTorch/YOLO
print("✓ Loading model...")
model = YOLO('yolov8s.pt')
print("✓ Model loaded")

# Test OpenCV
print("✓ Testing camera...")
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✓ Camera working")
    cap.release()
else:
    print("✗ Camera not available")

print("\nInstallation verification complete!")
```

Run test:
```bash
python test_installation.py
```

---

## Next Steps

After successful installation:
1. Update model path in `app/config.py`
2. Run `python app/main.py`
3. Test detection with your camera
4. Read [README.md](README.md) for usage guide
5. Check [app/README.md](app/README.md) for configuration

---

## 📞 Support

If you encounter issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review error messages carefully
3. Search GitHub issues
4. Create new GitHub issue with:
   - OS and Python version
   - Full error message
   - Steps to reproduce
   - System specs

---

## Additional Resources

- **Python**: https://www.python.org/downloads/
- **Git**: https://git-scm.com/
- **Virtual Environments**: https://docs.python.org/3/tutorial/venv.html
- **CUDA**: https://developer.nvidia.com/cuda-downloads
- **PyTorch**: https://pytorch.org/
- **YOLOv8**: https://docs.ultralytics.com/

---

**Last Updated**: January 28, 2026  
**Installation Guide Version**: 2.0  
**Status**: Current ✅
