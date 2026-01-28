# 📱 Application Module - Food Detection GUI

Main application folder containing all GUI components and detection logic for the Vietnamese food recognition system.

---

## 📁 Files Overview

### Core Files

#### [main.py](main.py) - Application Entry Point
```python
# Entry point of the application
from tkinter import Tk
from main_window import MainWindow

def main():
    """Khởi chạy ứng dụng"""
    root = Tk()
    app = MainWindow(root)
    root.mainloop()
```

**Usage**: 
```bash
cd app
python main.py
```

---

#### [main_window.py](main_window.py) - Primary GUI Window
Main window component that handles:
- Real-time camera feed display
- Detection canvas with bounding boxes
- Detection controls (Start/Stop)
- Confidence threshold slider
- Detected items list display

**Key Features**:
- Live video stream from webcam
- Real-time object detection
- Bounding box drawing with confidence scores
- FPS counter
- Smooth frame rendering

---

#### [result_screen.py](result_screen.py) - Results Display & Payment
Handles display of detected foods with:
- Grid layout (3 columns) for food cards
- Nutritional information display
- Confidence percentage
- Food descriptions
- Mouse wheel scrolling
- Payment system integration
- Invoice generation

**Features**:
- Compact food cards (400x250px each)
- Auto-wrapping to next row
- Smooth scrolling
- Price calculation
- Multiple payment methods
- Invoice history

---

#### [loading_screen.py](loading_screen.py) - Loading Animation
Professional loading screen displayed during:
- Application startup
- Model initialization
- Heavy processing

**Features**:
- Animated progress indicator
- Status messages
- Professional styling

---

#### [yolo_model.py](yolo_model.py) - YOLOv8 Model Wrapper
Wrapper class for YOLOv8 model handling:
- Model loading and initialization
- Inference and detection
- Confidence threshold management
- Batch processing
- GPU/CPU selection

**Key Methods**:
```python
class YOLOModel:
    def __init__(self, model_path):
        # Initialize model
        
    def predict(self, image, confidence=0.5):
        # Run detection on image
        
    def get_detections(self):
        # Get current detection results
```

---

#### [config.py](config.py) - Application Configuration
Central configuration file containing:
- Model paths
- Camera settings
- UI dimensions
- Color theme
- Detection parameters
- File paths

**Key Settings**:
```python
# Model
MODEL_PATH = r"path/to/best.pt"

# Camera
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# UI
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900

# Detection
DEFAULT_CONFIDENCE = 0.5
MIN_CONFIDENCE = 0.1
MAX_CONFIDENCE = 1.0

# Colors
COLORS = {
    'bg_dark': '#0f0f23',
    'accent_green': '#00ff88',
    # ... more colors
}
```

---

#### [image_utils.py](image_utils.py) - Image Processing
Utility functions for image manipulation:
- Image resizing and normalization
- Format conversion (BGR ↔ RGB)
- Histogram equalization
- Image enhancement
- Preprocessing for model input

**Common Functions**:
- `resize_image(image, width, height)`
- `normalize_image(image)`
- `draw_bounding_boxes(image, detections)`
- `enhance_image(image)`

---

#### [history_utils.py](history_utils.py) - Data Management
Handles persistence and retrieval of:
- Detection history
- Invoice records
- Transaction logs

**Key Functions**:
- `save_detection(detection_data)`
- `load_history(max_records=100)`
- `save_invoice(invoice_data)`
- `get_invoice_history()`

---

#### [__init__.py](__init__.py) - Package Initialization
Empty file marking this directory as a Python package.

---

## 🎨 Color Theme

Default color palette (customizable in [config.py](config.py)):

```python
COLORS = {
    'bg_dark': '#0f0f23',          # Dark background
    'bg_medium': '#16213e',        # Medium background
    'bg_header': '#1a1a2e',        # Header background
    'accent_green': '#00ff88',     # Green accent
    'accent_purple': '#6c5ce7',    # Purple accent
    'accent_blue': '#00b894',      # Blue accent
    'accent_red': '#ff6348',       # Red accent
    'accent_orange': '#ff4757',    # Orange accent
    'text_white': 'white',         # White text
    'text_gray': '#535c68'         # Gray text
}
```

---

## ⚙️ Configuration Guide

### Step 1: Update Model Path
Edit [config.py](config.py):
```python
MODEL_PATH = r"C:\path\to\your\best.pt"
```

### Step 2: Adjust Camera Settings (Optional)
```python
CAMERA_WIDTH = 1280      # Camera resolution width
CAMERA_HEIGHT = 720      # Camera resolution height
CAMERA_FPS = 30         # Frames per second
```

### Step 3: Customize UI Dimensions (Optional)
```python
WINDOW_WIDTH = 1600      # Main window width
WINDOW_HEIGHT = 900      # Main window height
CANVAS_WIDTH = 800       # Detection canvas width
CANVAS_HEIGHT = 550      # Detection canvas height
```

### Step 4: Set Detection Parameters (Optional)
```python
DEFAULT_CONFIDENCE = 0.5  # Default detection threshold
MIN_CONFIDENCE = 0.1      # Minimum slider value
MAX_CONFIDENCE = 1.0      # Maximum slider value
```

---

## 🔄 Data Flow

```
1. User clicks "Start Detection"
   ↓
2. main_window.py starts camera capture
   ↓
3. Frames sent to yolo_model.py for detection
   ↓
4. Detected items with confidence scores returned
   ↓
5. main_window.py draws bounding boxes on frame
   ↓
6. User clicks "View Results"
   ↓
7. result_screen.py displays detected foods in grid
   ↓
8. User selects items and proceeds to payment
   ↓
9. history_utils.py saves detection and invoice
   ↓
10. Invoice displayed and saved to disk
```

---

## 🚀 Running the Application

### Basic Start
```bash
cd app
python main.py
```

### With Custom Config
Create a backup of [config.py](config.py) and modify settings as needed.

### Debug Mode
Add debugging to any module by uncommenting print statements or adding logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

---

## 📊 Main Window Features

### Detection Controls
- **Start Button**: Begin camera capture and detection
- **Stop Button**: Stop detection and close camera
- **Confidence Slider**: Adjust detection threshold (10% - 100%)
- **FPS Counter**: Real-time frame rate display

### Display Elements
- **Camera Feed**: Live video stream (800x550px)
- **Detected Items**: List of recognized foods
- **Bounding Boxes**: Visual indicators with confidence
- **Status Bar**: Current mode and statistics

---

## 💳 Payment System

### Supported Methods
1. **Cash Payment** - Direct payment
2. **Credit/Debit Card** - Card payment processing
3. **Mobile Payment** - Digital wallet options

### Invoice Components
- Unique invoice ID
- Timestamp
- Itemized list of detected foods
- Price breakdown
- Total calories
- Payment method
- Thank you message

---

## 📝 Detected Items Storage

### In-Memory Storage
- Current detection session stored in variables
- Quick access during active session

### Persistent Storage
- `detection_history.json`: All detection records
- `invoice_history.json`: All transaction records
- `invoices/`: Individual invoice text files

---

## 🔧 Troubleshooting

### Model Not Loading
1. Check [config.py](config.py) `MODEL_PATH`
2. Verify file exists at path
3. Ensure `.pt` file has correct permissions

### Camera Not Working
1. Check camera connection
2. Verify camera permissions (Windows/Mac/Linux)
3. Try different camera index in code
4. Restart application

### Low Detection Accuracy
1. Increase lighting conditions
2. Reduce `CAMERA_FPS` if unstable
3. Retrain model with more data
4. Adjust `DEFAULT_CONFIDENCE` threshold

### UI Display Issues
1. Check `WINDOW_WIDTH` and `WINDOW_HEIGHT` in config
2. Ensure sufficient screen resolution
3. Update graphics drivers
4. Reinstall Tkinter

---

## 💡 Development Tips

### Adding New Features
1. Create new `.py` file in `app/` folder
2. Import necessary modules
3. Use existing utilities from [image_utils.py](image_utils.py) and [history_utils.py](history_utils.py)
4. Integrate with [main_window.py](main_window.py)

### Debugging
```python
# Add debug prints
print(f"Detection: {detection_results}")

# Use logging
import logging
logging.info("Model loaded successfully")
```

### Performance Optimization
- Use GPU acceleration (CUDA)
- Reduce image resolution
- Optimize inference batch size
- Profile code for bottlenecks

---

## 📦 Dependencies

All required packages listed in [../requirements.txt](../requirements.txt):
- **opencv-python**: Image processing
- **Pillow**: Image manipulation
- **ultralytics**: YOLOv8 framework
- **qrcode**: QR code generation (for invoices)
- **tkinter**: GUI framework (built-in Python)

---

## 🎯 Next Steps

1. **Configure paths** in [config.py](config.py)
2. **Verify model location** and accessibility
3. **Test camera** connection
4. **Run application**: `python main.py`
5. **Start detection** and verify results
6. **Test payment** flow
7. **Check invoice** generation

---

## 📞 Support

For issues or questions:
1. Check [config.py](config.py) for correct paths
2. Verify dependencies in `pip list`
3. Check console output for error messages
4. Review ../README.md for general guidance

---

**Last Updated**: January 28, 2026  
**Module Version**: 2.0  
**Status**: Production Ready ✅
