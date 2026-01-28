# utils/image_utils.py
"""
Các hàm tiện ích xử lý ảnh
"""
import cv2
from PIL import Image, ImageTk

def resize_image_to_canvas(img, canvas_width, canvas_height):
    """
    Resize ảnh để fit vào canvas
    
    Args:
        img: Ảnh đầu vào (numpy array BGR)
        canvas_width: Chiều rộng canvas
        canvas_height: Chiều cao canvas
        
    Returns:
        img_tk: Ảnh đã resize dạng ImageTk
        new_w, new_h: Kích thước mới
    """
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    h, w = img_rgb.shape[:2]
    
    scale = min(canvas_width/w, canvas_height/h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    img_resized = cv2.resize(img_rgb, (new_w, new_h))
    img_pil = Image.fromarray(img_resized)
    img_tk = ImageTk.PhotoImage(img_pil)
    
    return img_tk, new_w, new_h

def load_image(file_path):
    """
    Load ảnh từ file path
    
    Args:
        file_path: Đường dẫn file
        
    Returns:
        img: Ảnh dạng numpy array hoặc None nếu lỗi
    """
    try:
        img = cv2.imread(file_path)
        return img
    except Exception as e:
        print(f"❌ Lỗi load ảnh {file_path}: {e}")
        return None