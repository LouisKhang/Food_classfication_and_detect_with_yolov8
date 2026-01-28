# Food Detection System - Getting Started Guide

Hướng dẫn toàn diện cho người mới tải về dự án.

---

## Dự Án Là Gì?

Đây là một hệ thống nhận diện thực phẩm Việt Nam sử dụng AI (YOLOv8). Ứng dụng có thể:

- Nhận diện 30 loại đặc sản Việt Nam qua camera
- Hiển thị thông tin dinh dưỡng từng món ăn
- Tính toán giá tiền tự động
- Hỗ trợ thanh toán và xuất hóa đơn
- Lưu lịch sử phát hiện

**Ví dụ:** Bạn chỉ máy ảnh vào một bát phở, hệ thống sẽ nhận diện là "Phở", hiển thị giá tiền, calories, và các thông tin khác.

---

## Yêu Cầu Hệ Thống

### Tối thiểu:
- Windows, macOS, hoặc Linux
- Python 3.8 trở lên
- Webcam hoặc camera USB
- 4GB RAM
- 2GB dung lượng trống

### Khuyến nghị:
- Python 3.10 hoặc 3.11
- 8GB RAM
- NVIDIA GPU (tùy chọn, để chạy nhanh hơn)

---

## Cài Đặt Nhanh (5 Phút)

### Bước 1: Tải Python

1. Vào https://www.python.org/downloads/
2. Tải Python 3.10 hoặc 3.11
3. Cài đặt và **đánh dấu "Add Python to PATH"**

**Kiểm tra:**
```bash
python --version
```

Nếu không nhận, khởi động lại máy.

---

### Bước 2: Tải Dự Án

**Cách 1: Dùng Git**
```bash
git clone https://github.com/yourusername/food_detection.git
cd food_selected_pho_bun
```

**Cách 2: Tải ZIP**
1. Click "Code" → "Download ZIP" trên GitHub
2. Giải nén file
3. Mở Command Prompt trong thư mục đó

---

### Bước 3: Tạo Môi Trường Ảo

```bash
# Tạo thư mục ảo
python -m venv venv

# Kích hoạt (Windows)
venv\Scripts\activate

# Kích hoạt (macOS/Linux)
source venv/bin/activate
```

Sau khi chạy, dòng lệnh sẽ có `(venv)` ở đầu.

---

### Bước 4: Cài Đặt Thư Viện

```bash
# Cập nhật pip
pip install --upgrade pip

# Cài đặt yêu cầu
pip install -r requirements.txt
```

Chờ khoảng 2-3 phút cho quá trình cài.

---

### Bước 5: Cấu Hình Đường Dẫn Model

1. Mở file `app/config.py` bằng text editor (Notepad, VS Code, v.v)
2. Tìm dòng có `MODEL_PATH`
3. Thay đổi thành đường dẫn đúng của model:

```python
MODEL_PATH = r"C:\Users\YourUsername\Downloads\food_selected_pho_bun\food_detection_36class_1100\food_detection_36class_1100_resume\yolov8s_vietfood_36class_1100\weights\best.pt"
```

Hoặc nếu bạn có file `best.pt` ở nơi khác, dùng đường dẫn đó.

---

### Bước 6: Chạy Ứng Dụng

```bash
cd app
python main.py
```

Nếu thấy cửa sổ ứng dụng mở ra = thành công!

---

## Sử Dụng Ứng Dụng

### Giao Diện Chính

1. **Nút "Start Detection"**: Bắt đầu camera
2. **Nút "Stop Detection"**: Dừng camera
3. **Thanh trượt (Slider)**: Điều chỉnh độ nhạy (0.1 - 1.0)
4. **Hiển thị video**: Xem camera real-time

### Quy Trình Sử Dụng

```
1. Click "Start Detection"
   ↓
2. Chỉ camera vào đồ ăn
   ↓
3. Hệ thống nhận diện tự động
   ↓
4. Chọn "View Results" để xem chi tiết
   ↓
5. Click "THANH TOÁN" để xuất hóa đơn
   ↓
6. Lưu hóa đơn vào thư mục invoices/
```

---

## Thư Mục Dự Án

```
food_selected_pho_bun/
├── app/                          # Ứng dụng chính
│   ├── main.py                   # Chạy file này
│   ├── config.py                 # Cấu hình (thay đổi đường dẫn model ở đây)
│   ├── main_window.py            # Giao diện chính
│   ├── yolo_model.py             # Model AI
│   └── ...
│
├── dataset/                       # Dữ liệu huấn luyện
│   ├── images/                   # Ảnh
│   └── labels/                   # Nhãn
│
├── food_detection_36class_1100/   # Model đã huấn luyện
│   └── yolov8s_vietfood_36class_1100/
│       └── weights/
│           └── best.pt           # File model chính
│
├── README.md                      # Tài liệu chi tiết
├── INSTALLATION.md               # Hướng dẫn cài đặt
├── QUICKSTART.md                 # File này
├── requirements.txt              # Thư viện cần cài
└── UPDATES.md                    # Cập nhật mới
```

---

## Danh Sách 30 Món Ăn Được Hỗ Trợ

| # | Tên Tiếng Việt | Tên Tiếng Anh |
|---|---|---|
| 1 | Bánh Bèo | Steamed rice cake |
| 2 | Bánh Bột Lọc | Tapioca cake |
| 3 | Bánh Căn | Small round cake |
| 4 | Bánh Canh | Tapioca with meat |
| 5 | Bánh Chưng | Square rice cake |
| 6 | Bánh Cuốn | Rolled rice cake |
| 7 | Bánh Đức | Steamed tapioca |
| 8 | Bánh Giò | Fried pyramid cake |
| 9 | Bánh Khot | Tiny round cake |
| 10 | Bánh Mì | Vietnamese sandwich |
| 11 | Bánh Pía | Bánh Pía pastry |
| 12 | Bánh Tết | Tet cake |
| 13 | Bánh Tráng Nướng | Grilled rice paper |
| 14 | Bánh Xèo | Sizzling pancake |
| 15 | Bún Bò Huế | Huế beef noodle |
| 16 | Bún Đậu Mắm Tôm | Noodle with shrimp |
| 17 | Bún Mắm | Fish sauce noodle |
| 18 | Bún Riêu | Crab noodle soup |
| 19 | Bún Thịt Nướng | Grilled pork noodle |
| 20 | Cá Kho Tộ | Braised fish |
| 21 | Canh Chua | Sweet sour soup |
| 22 | Cao Lầu | Quang noodle |
| 23 | Cháo Lòng | Rice porridge |
| 24 | Cơm Tấm | Broken rice |
| 25 | Gỏi Cuốn | Fresh spring roll |
| 26 | Hủ Tiếu | Clear noodle soup |
| 27 | Mì Quảng | Quang noodle |
| 28 | Nem Chua | Sour sausage |
| 29 | Phở | Beef noodle soup |
| 30 | Xôi Xéo | Sticky rice |

---

## Giải Quyết Vấn Đề Thường Gặp

### 1. Python không nhận được

**Vấn đề:** Gõ `python --version` nhưng không nhận

**Giải pháp:**
- Windows: Gỡ cài và cài lại, đánh dấu "Add Python to PATH"
- macOS/Linux: Dùng `python3` thay vì `python`

---

### 2. Module không tìm được

**Vấn đề:** Lỗi `ModuleNotFoundError: No module named 'cv2'`

**Giải pháp:**
```bash
# Kiểm tra môi trường ảo được kích hoạt
# Dòng lệnh phải có (venv) ở đầu

# Cài lại thư viện
pip install -r requirements.txt --force-reinstall
```

---

### 3. Camera không hoạt động

**Vấn đề:** Ứng dụng mở nhưng camera không chạy

**Giải pháp:**
- Windows: Kiểm tra Device Manager, cập nhật driver camera
- macOS: System Preferences → Security & Privacy → Camera (cho phép)
- Linux: `sudo usermod -a -G video $USER` rồi khởi động lại

---

### 4. Model không tìm được

**Vấn đề:** Lỗi `FileNotFoundError: No such file or directory`

**Giải pháp:**
1. Mở `app/config.py`
2. Kiểm tra `MODEL_PATH` có đúng không
3. Thử dùng absolute path (đường dẫn đầy đủ)
4. File `best.pt` có tồn tại không?

---

### 5. Ứng dụng chạy chậm

**Vấn đề:** FPS thấp, phát hiện chậm

**Giải pháp:**
```python
# Mở app/config.py, giảm độ phân giải:
CAMERA_WIDTH = 640   # Thay từ 1280
CAMERA_HEIGHT = 480  # Thay từ 720
```

---

### 6. "Out of Memory" Error

**Vấn đề:** Ứng dụng bị crash, hết bộ nhớ

**Giải pháp:**
- Đóng các ứng dụng khác
- Giảm độ phân giải camera (xem phần 5)
- Nếu có GPU, kiểm tra đủ VRAM không

---

## Cấu Hình Tùy Chỉnh

### Thay Đổi Tốc Độ Camera

File: `app/config.py`

```python
CAMERA_WIDTH = 1280      # Độ rộng
CAMERA_HEIGHT = 720      # Độ cao
CAMERA_FPS = 30         # Khung hình/giây
```

**Gợi ý:**
- 1280x720: Chất lượng cao, chậm hơn
- 640x480: Nhanh hơn, chất lượng thấp

---

### Thay Đổi Độ Nhạy Mặc Định

File: `app/config.py`

```python
DEFAULT_CONFIDENCE = 0.5  # 0.1 = nhạy hơn, 1.0 = chặt hơn
MIN_CONFIDENCE = 0.1      # Tối thiểu
MAX_CONFIDENCE = 1.0      # Tối đa
```

---

### Thay Đổi Giao Diện

File: `app/config.py`

```python
WINDOW_WIDTH = 1600       # Chiều rộng cửa sổ
WINDOW_HEIGHT = 900       # Chiều cao cửa sổ

COLORS = {
    'bg_dark': '#0f0f23',       # Nền tối
    'accent_green': '#00ff88',  # Xanh lá
    'accent_purple': '#6c5ce7', # Tím
    # ... và nhiều màu khác
}
```

---

## Thư Mục Kết Quả

Sau mỗi lần sử dụng, ứng dụng lưu:

### Lịch Sử Phát Hiện
```
detection_history.json    # Lưu trữ tất cả phát hiện
```

### Hóa Đơn
```
invoices/
├── invoice_20260128_143022.txt    # Hóa đơn 28/01/2026 14:30:22
├── invoice_20260128_143145.txt
└── ...

invoice_history.json      # Lịch sử tất cả hóa đơn
```

Bạn có thể xem lại những gì đã lưu trong các file này.

---

## Câu Hỏi Thường Gặp

### Q: Làm sao để thêm más ăn mới?

A: Xem file `INSTALLATION.md` hoặc `dataset/README.md` để huấn luyện model với dữ liệu mới.

---

### Q: Có thể dùng camera ngoài không?

A: Có. Hệ thống tự nhận diện camera có sẵn. Nếu có nhiều camera, chỉnh chỉ số camera trong code.

---

### Q: Model nào tốt nhất?

A: Hiện tại có:
- **36-class (1100 ảnh)**: Tốc độ nhanh, độ chính xác tốt (khuyên dùng)
- **49-class (800 ảnh)**: Nhiều loại hơn, chậm hơn
- **VIP 31-class (5000 ảnh)**: Chính xác nhất, chậm nhất

---

### Q: Có thể chạy trên mobile/web không?

A: Hiện tại là ứng dụng desktop. Mobile và web sẽ được phát triển sau.

---

### Q: Cần GPU không?

A: Không bắt buộc. Chạy trên CPU (RAM) cũng được, nhưng chậm hơn. Nếu có GPU NVIDIA, hệ thống sẽ tự dùng.

---

### Q: Dữ liệu được gửi đi đâu không?

A: Không. Mọi thứ chạy cục bộ trên máy bạn. Không có kết nối internet.

---

## Các Tệp Tài Liệu Khác

| File | Mục Đích |
|------|---------|
| `README.md` | Tài liệu chi tiết, đầy đủ |
| `INSTALLATION.md` | Hướng dẫn cài đặt từng OS |
| `app/README.md` | Chi tiết các file trong app/ |
| `dataset/README.md` | Cách sử dụng dataset, huấn luyện |
| `CONTRIBUTING.md` | Cách đóng góp vào dự án |
| `UPDATES.md` | Các tính năng mới |

---

## Liên Hệ & Hỗ Trợ

- Kiểm tra `README.md` để biết thêm chi tiết
- Đọc `INSTALLATION.md` nếu có vấn đề cài đặt
- Xem `UPDATES.md` để biết tính năng mới

---

## Bước Tiếp Theo

1. **Cài đặt xong rồi?**
   ```bash
   cd app
   python main.py
   ```

2. **Muốn thêm ảnh/datos?**
   - Xem `dataset/README.md`

3. **Muốn sửa code?**
   - Xem `app/README.md`

4. **Muốn đóng góp?**
   - Xem `CONTRIBUTING.md`

---

## Chúc Mừng!

Bạn đã cài đặt thành công Food Detection System. Giờ hãy thử:

```bash
cd app
python main.py
```

Chỉ camera vào một món ăn Việt Nam và xem hệ thống nhận diện nó!

---

**Ngày cập nhật:** 28/01/2026  
**Phiên bản:** 2.0  
**Trạng thái:** Sẵn sàng sử dụng ✅

Chúc bạn thành công!
