# Food Detection & Recognition System (Vietnamese Cuisine)

A comprehensive AI-powered food detection and recognition system specialized in Vietnamese cuisine using YOLOv8 object detection. This project includes a real-time detection application with GUI, payment system, and invoice management.

**Language:** Vietnamese Cuisine Detection  
**Model:** YOLOv8s (Small)  
**Framework:** PyTorch + Ultralytics  
**UI:** Tkinter (Python)

---

## Features

### Core Detection Features
- **Real-time Food Detection**: Detect up to 36 Vietnamese food items using webcam/camera input
- **High Accuracy**: Trained models with 30 Vietnamese food classes
- **Multiple Model Variants**: 
  - 36-class model with 1100+ training images
  - 49-class model with 800+ training images
  - Specialized VIP model with 31 classes

### GUI Application Features
- **Live Detection**: Real-time camera feed with bounding boxes and confidence scores
- **Detection Results**: Grid-based layout showing detected foods with:
  - Food name and confidence percentage
  - Nutritional information (calories)
  - Food descriptions
  - Detailed nutrition charts
-- **Payment System**: 
  - Support for cash, credit card, and mobile payment methods
  - Real-time price calculation
-- **Invoice Management**:
  - Auto-generate and save invoices
  - Store transaction history in JSON format
  - Printable invoice format
- **Detection History**: Track all detections with timestamps

### Technical Features
- Efficient model loading and inference
- Image preprocessing and normalization
- Confidence threshold adjustment (10% - 100%)
- Responsive UI with dark theme
- Multi-threaded detection for smooth performance

---

## Project Structure

```
food_selected_pho_bun/
├── README.md                          # Main documentation
├── requirements.txt                   # Python dependencies
├── data.yaml                          # Dataset configuration
├── UPDATES.md                         # Latest updates and features
├── yolov8s.pt                         # Base YOLOv8s model (optional)
├── food_36.json                       # Food database (36 classes)
├── food_36.json                       # Food database (36 classes)
├── detection_history.json             # Detection records
├── test_normalization.py              # Image normalization tests
│
├── app/                               # Main application folder
│   ├── main.py                        # Entry point
│   ├── main_window.py                 # Main GUI window
│   ├── result_screen.py               # Results display screen
│   ├── loading_screen.py              # Loading animation screen
│   ├── config.py                      # Application configuration
│   ├── yolo_model.py                  # YOLOv8 model wrapper
│   ├── image_utils.py                 # Image processing utilities
│   ├── history_utils.py               # Detection history management
│   └── __init__.py                    # Package initialization
│
├── dataset/                           # Training dataset
│   ├── data.yaml                      # Dataset paths and classes
│   ├── images/
│   │   ├── train/                     # Training images
│   │   ├── valid/                     # Validation images
│   │   └── test/                      # Test images
│   ├── labels/
│   │   ├── train/                     # Training annotations (YOLO format)
│   │   ├── valid/                     # Validation annotations
│   │   └── test/                      # Test annotations
│   └── food_detection/
│       └── food_detection.py          # Dataset utilities
│
├── food_detection_36class_1100/       # 36-class model (1100 images)
│   ├── food_detection_36class_1100/   # Training results
│   └── food_detection_36class_1100_resume/  # Resumed training
│
├── food_detection_49class_800/        # 49-class model (800 images)
│   ├── food_detection_49class/        # Training results
│   └── food_detection_49class_resume/ # Resumed training
│
├── yolov8s_vietfood_dataset_31class_5000_image/  # VIP model
│   └── yolov8s_vietfood_VIP/
│
├── runs/                              # Detection results
│   └── detect/                        # All prediction outputs
│       ├── predict/
│       ├── predict1/
│       ├── predict2/
│       └── ... (48 more prediction folders)
│
├── web/                               # Web assets
│   └── payment_success.html           # Payment confirmation page
│
└── training notebooks/
    ├── food_detection_train3.ipynb    # Training script
    ├── food_split_dataset.ipynb       # Dataset splitting script
    └── food_detection_train_*.ipynb   # Various training experiments
```

---

## Supported Vietnamese Dishes (30 Classes)

| No. | Dish Name | English Name |
|-----|-----------|--------------|
| 1 | Bánh Bèo | Steamed rice cake with shrimp |
| 2 | Bánh Bột Lọc | Tapioca cake |
| 3 | Bánh Căn | Small round cake |
| 4 | Bánh Canh | Tapioca cake with meat |
| 5 | Bánh Chưng | Square rice cake |
| 6 | Bánh Cuốn | Rolled rice cake |
| 7 | Bánh Đức | Steamed tapioca cake |
| 8 | Bánh Giò | Fried pyramid cake |
| 9 | Bánh Khot | Tiny round cake |
| 10 | Bánh Mì | Vietnamese sandwich |
| 11 | Bánh Pía | Bánh Pía pastry |
| 12 | Bánh Tết | Tet cake |
| 13 | Bánh Tráng Nướng | Grilled rice paper |
| 14 | Bánh Xèo | Sizzling pancake |
| 15 | Bún Bò Huế | Huế beef noodle soup |
| 16 | Bún Đậu Mắm Tôm | Bean sprout noodle with shrimp paste |
| 17 | Bún Mắm | Noodle soup with fish sauce |
| 18 | Bún Riêu | Crab noodle soup |
| 19 | Bún Thịt Nướng | Grilled pork noodle |
| 20 | Cá Kho Tộ | Braised fish in clay pot |
| 21 | Canh Chua | Sweet and sour soup |
| 22 | Cao Lầu | Quang specialty noodle |
| 23 | Cháo Lòng | Offal rice porridge |
| 24 | Cơm Tấm | Broken rice |
| 25 | Gỏi Cuốn | Fresh spring roll |
| 26 | Hủ Tiếu | Clear noodle soup |
| 27 | Mì Quảng | Quang specialty noodle |
| 28 | Nem Chua | Sour sausage |
| 29 | Phở | Beef noodle soup |
| 30 | Xôi Xéo | Sticky rice with young corn |

---

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows, macOS, or Linux
- Webcam/Camera for real-time detection

### Step 1: Clone or Download the Project
```bash
git clone https://github.com/yourusername/food_detection.git
cd food_selected_pho_bun
```

### Step 2: Create Virtual Environment (Optional but Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Update Model Path in Config
Edit [app/config.py](app/config.py) and update the `MODEL_PATH`:
```python
MODEL_PATH = r"path/to/your/best.pt"
```

The pre-trained model should be located at:
```
food_detection_36class_1100/food_detection_36class_1100_resume/yolov8s_vietfood_36class_1100/weights/best.pt
```

---

## 📖 Usage

### Running the Application
```bash
# Navigate to app directory
cd app

# Run the main application
python main.py
```

### Application Workflow
1. **Start Detection**: Application opens with main window
2. **Camera Input**: Select camera source
3. **Real-time Detection**: System detects foods with confidence scores
4. **View Results**: Detected foods displayed in grid layout
5. **Payment**: Select detected items and proceed to payment
6. **Invoice**: Generate and save transaction receipt

### Configuration Options
Edit [app/config.py](app/config.py) to customize:
- **Camera settings**: Resolution, FPS
- **UI dimensions**: Window size, canvas size
- **Color theme**: Accent colors and backgrounds
- **Confidence threshold**: Default detection confidence
- **File paths**: Model location, data files

---

## Configuration

### app/config.py Key Settings

```python
# Model Path
MODEL_PATH = r"path/to/best.pt"

# Camera Settings
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# UI Settings
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900

# Detection
DEFAULT_CONFIDENCE = 0.5
MIN_CONFIDENCE = 0.1
MAX_CONFIDENCE = 1.0
```

### data.yaml Structure
```yaml
train: train/images
val: valid/images
test: test/images
nc: 30  # Number of classes
names:
  - Bánh Bèo
  - Bánh Bột Lọc
  # ... (more classes)
```

---

## Model Information

### Current Models
- **36-class Model**: Best for pho and bun specialties (1100+ training images)
- **49-class Model**: Extended food categories (800+ training images)  
- **VIP Model**: Premium 31-class model (5000+ training images)

### Model Performance
- **Architecture**: YOLOv8s (Small)
- **Input Size**: 640×640 pixels
- **Framework**: PyTorch + Ultralytics
- **Inference Speed**: ~40-50ms per frame (GPU) / ~100-150ms (CPU)

### Training Details
Training notebooks available:
- [food_detection_train3.ipynb](food_detection_train3.ipynb)
- [food_split_dataset.ipynb](food_split_dataset.ipynb)
- Additional training experiments in training subdirectories

---

## Data Management

### Detection History
Automatically saved to `detection_history.json`:
```json
{
  "detection_id": "DET_20260128_143022",
  "timestamp": "28/01/2026 14:30:22",
  "items": [
    {
      "name": "Phở",
      "confidence": 0.95,
      "calories": 520
    }
  ]
}
```

### Invoice Management
Invoices stored in:
- **Text Format**: `invoices/invoice_YYYYMMDD_HHMMSS.txt`
- **JSON History**: `invoice_history.json`

---

## UI Features

### Main Window
- Dark theme with accent colors (green, purple, blue)
- Real-time camera feed display
- Confidence threshold slider
- Start/Stop detection buttons

### Result Screen
- Grid layout (3 columns)
- Food cards with:
  - Thumbnail image
  - Confidence percentage
  - Nutrition information
  - Food description
  - Price information
- Mouse wheel scrolling support
- Payment button at bottom

### Loading Screen
- Professional loading animation
- Model initialization status
- Progress indicators

---

## 📝 Important Files

| File | Purpose |
|------|---------|
| [app/main.py](app/main.py) | Application entry point |
| [app/main_window.py](app/main_window.py) | Main GUI window with detection |
| [app/result_screen.py](app/result_screen.py) | Results display and payment |
| [app/yolo_model.py](app/yolo_model.py) | YOLOv8 model wrapper |
| [app/config.py](app/config.py) | Configuration settings |
| [app/image_utils.py](app/image_utils.py) | Image processing functions |
| [app/history_utils.py](app/history_utils.py) | History and data management |
| [data.yaml](data.yaml) | Dataset configuration |
| [requirements.txt](requirements.txt) | Python dependencies |

---

## 🐛 Troubleshooting

### Model Not Found
- Check `MODEL_PATH` in [app/config.py](app/config.py)
- Ensure `.pt` file exists at specified location
- Download pre-trained weights if missing

### Camera Issues
- Verify camera is connected and recognized by system
- Check camera permissions (Windows/macOS/Linux)
- Try different camera indices in code

### Low Confidence Results
- Adjust `DEFAULT_CONFIDENCE` in config.py (default: 0.5)
- Ensure good lighting conditions
- Train model with more diverse images

### UI Not Displaying Correctly
- Check resolution settings in config.py
- Ensure Tkinter is properly installed
- Update display driver

### Memory Issues
- Reduce `CAMERA_WIDTH` and `CAMERA_HEIGHT`
- Use CPU instead of GPU if VRAM is limited
- Reduce batch size for detection

---

## Performance Metrics

- **FPS**: 20-30 FPS on GPU, 5-10 FPS on CPU
- **Accuracy**: 85-95% confidence on well-lit images
- **Inference Time**: ~50ms per frame
- **Memory Usage**: ~2GB GPU, ~1GB RAM CPU mode

---

## 🔄 Latest Updates

See [UPDATES.md](UPDATES.md) for detailed changelog:
- ✅ Grid layout for result display
- ✅ Mouse wheel scrolling
- ✅ Payment system integration
- ✅ Invoice generation and history
- ✅ Enhanced UI with compact cards
- ✅ Nutritional information display

---

## Training & Dataset

### Dataset Structure
```
dataset/
├── images/
│   ├── train/     (training images)
│   ├── valid/     (validation images)
│   └── test/      (test images)
├── labels/
│   ├── train/     (YOLO format annotations)
│   ├── valid/
│   └── test/
└── data.yaml      (dataset config)
```

### Training a New Model
1. Prepare dataset in YOLO format
2. Update [dataset/data.yaml](dataset/data.yaml)
3. Use training notebooks:
   ```bash
   jupyter notebook food_detection_train3.ipynb
   ```
4. Monitor training results in `runs/detect/`

---

## 🔐 File Paths Configuration

Update these paths for your system:

**In [app/config.py](app/config.py)**:
```python
# Model path - update to your model location
MODEL_PATH = r"C:\path\to\best.pt"

# Food database - update to your data location
FOOD_DATA_FILE = r"C:\path\to\food_36.json"

# History file - can be relative or absolute
HISTORY_FILE = "detection_history.json"
```

---

## Contributing

Contributions are welcome! To contribute:
1. Create a feature branch
2. Make your improvements
3. Test thoroughly
4. Submit a pull request

Areas for enhancement:
- Support for more food classes
- Mobile app version
- Cloud-based deployment
- Multi-language support
- Advanced analytics

---

## License

This project is for educational and commercial use.

---

## 📧 Contact & Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Check existing documentation
- Review [UPDATES.md](UPDATES.md) for recent changes

---

## References

- **YOLOv8**: https://github.com/ultralytics/ultralytics
- **PyTorch**: https://pytorch.org/
- **OpenCV**: https://opencv.org/
- **Tkinter**: https://docs.python.org/3/library/tkinter.html

---

## Acknowledgments

This project was developed for Vietnamese cuisine detection and recognition. Special thanks to:
- Ultralytics for YOLOv8
- The open-source community
- All contributors and testers

---

**Last Updated**: January 28, 2026  
**Version**: 2.0 (With Payment & Invoice System)  
**Status**: Active Development ✅
