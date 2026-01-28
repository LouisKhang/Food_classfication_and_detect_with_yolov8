# main_window.py
"""
Cửa sổ chính của ứng dụng Food Detection - Tất cả UI trong 1 cửa sổ
"""
import cv2
from tkinter import *
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import socket
import threading
import math

import config
from yolo_model import YOLOModelManager
from image_utils import resize_image_to_canvas, load_image
from history_utils import HistoryManager

try:
    import qrcode
    from PIL import Image, ImageTk
    HAS_QR = True
except ImportError:
    HAS_QR = False

# Thư mục gốc project (chứa app/ và web/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAYMENT_HTML_PATH = PROJECT_ROOT / "web" / "payment_success.html"
PAYMENT_SERVER_PORT = 8765


def _get_local_ip():
    """Lấy IP nội bộ (Wi‑Fi/LAN) để điện thoại cùng mạng mở được link trong QR."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _make_payment_handler(app_ref):
    """Tạo lớp Handler có tham chiếu tới MainWindow."""
    class PaymentHTTPHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Tắt log request
        def do_GET(self):
            path = urlparse(self.path).path
            query = parse_qs(urlparse(self.path).query)
            method = (query.get("m") or ["vietqr"])[0]
            if path in ("/success", "/"):
                try:
                    html_path = PAYMENT_HTML_PATH
                    if html_path.exists():
                        body = html_path.read_bytes()
                    else:
                        body = b"<h1>Thanh toan thanh cong!</h1>"
                except Exception:
                    body = b"<h1>Thanh toan thanh cong!</h1>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                if app_ref and getattr(app_ref, "root", None):
                    app_ref.root.after(0, lambda: app_ref.on_payment_success_from_web(method))
                return
            self.send_response(404)
            self.end_headers()
    return PaymentHTTPHandler


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("🍕 Food Detection AI - YOLOv8 (Multi-Image)")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.configure(bg=config.COLORS['bg_dark'])
        
        # Load model
        self.model_manager = YOLOModelManager()
        
        # Load food data từ food_36.json
        self.food_data = self.load_food_data()
        
        # History manager
        self.history_manager = HistoryManager()
        
        # Variables
        self.cap = None
        self.is_camera_running = False
        self.current_image = None
        self.confidence_threshold = config.DEFAULT_CONFIDENCE
        
        # Multi-image variables
        self.uploaded_images = []
        self.current_index = 0
        
        # Current detections (cho result screen)
        self.current_detections = []
        
        # Screen states
        self.current_screen = "main"  # "main", "loading", "result"
        
        # Frames
        self.main_frame = None
        self.loading_frame = None
        self.result_frame = None
        
        # Store for animation
        self.loading_angle = 0
        self.is_loading_active = False
        
        # Payment: server link + cửa sổ thanh toán (để đóng khi web xác nhận)
        self._payment_window = None
        self._payment_server_url = None
        self._start_payment_server()
        
        self.setup_ui()
    
    def load_food_data(self):
        """Load dữ liệu món ăn từ JSON"""
        try:
            if os.path.exists(config.FOOD_DATA_FILE):
                with open(config.FOOD_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️ Không tìm thấy file {config.FOOD_DATA_FILE}")
                return {}
        except Exception as e:
            print(f"❌ Lỗi load food data: {e}")
            return {}
    
    def _start_payment_server(self):
        """Chạy server HTTP nền để phục vụ trang thanh toán thành công khi quét QR."""
        try:
            local_ip = _get_local_ip()
            handler = _make_payment_handler(self)
            self._httpd = HTTPServer(("0.0.0.0", PAYMENT_SERVER_PORT), handler)
            self._httpd.app_ref = self
            self._payment_server_url = f"http://{local_ip}:{PAYMENT_SERVER_PORT}/success"
            t = threading.Thread(target=self._httpd.serve_forever, daemon=True)
            t.start()
            print(f"✅ Payment server: {self._payment_server_url}")
        except Exception as e:
            print(f"⚠️ Không chạy được payment server: {e}")
            self._payment_server_url = None
    
    def on_payment_success_from_web(self, method):
        """Gọi từ server khi điện thoại mở link thanh toán → xuất hóa đơn, đóng dialog, cập nhật UI."""
        name_map = {"cash": "Tiền mặt", "momo": "Momo", "zalopay": "ZaloPay", "vietqr": "VietQR"}
        method_name = name_map.get(method, method)
        if getattr(self, "current_detections", None):
            path = self.save_invoice_to_downloads(method_name)
            msg = f"Đã nhận xác nhận từ trình duyệt.\n\nHóa đơn đã lưu:\n{path}"
        else:
            msg = "Đã nhận xác nhận từ trình duyệt.\n\nChưa có đơn hàng để xuất hóa đơn."
        if getattr(self, "_payment_window", None):
            try:
                if self._payment_window.winfo_exists():
                    self._payment_window.destroy()
            except Exception:
                pass
            self._payment_window = None
        messagebox.showinfo("Thanh toán thành công", msg)
    
    def setup_ui(self):
        """Thiết kế giao diện chính"""
        # Container chính
        self.container = Frame(self.root, bg=config.COLORS['bg_dark'])
        self.container.pack(fill=BOTH, expand=True)
        
        # Tạo các frame cho mỗi screen
        self.create_main_screen()
        self.create_loading_screen()
        self.create_result_screen()
        
        # Hiển thị main screen
        self.show_screen("main")
    
    def create_main_screen(self):
        """Tạo màn hình chính"""
        self.main_frame = Frame(self.container, bg=config.COLORS['bg_dark'])
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # ============= HEADER =============
        header_frame = Frame(self.main_frame, bg=config.COLORS['bg_header'], height=80)
        header_frame.pack(fill=X, padx=10, pady=10)
        
        title_label = Label(
            header_frame, 
            text="🍕 FOOD DETECTION AI - MULTI IMAGE", 
            font=("Arial", 26, "bold"),
            bg=config.COLORS['bg_header'], 
            fg=config.COLORS['accent_green']
        )
        title_label.pack(pady=15)

        # Nút "Xem kết quả" — chỉ hiện khi đã có kết quả nhận diện
        self.btn_see_result = Button(
            header_frame,
            text="📊 Xem kết quả",
            bg=config.COLORS['accent_green'],
            fg='white',
            font=('Arial', 10, 'bold'),
            bd=0,
            padx=16,
            pady=6,
            cursor='hand2',
            command=lambda: self.show_screen("result")
        )
        # Đặt bên phải header (pack sau title rồi pack_slave hoặc dùng place). Dùng place cho gọn.
        self.btn_see_result.place(relx=1.0, rely=0.5, anchor=E, x=-10)
        self.btn_see_result.place_forget()  # Ẩn lúc đầu, hiện khi có current_detections
        
        # ============= MAIN CONTAINER =============
        main_container = Frame(self.main_frame, bg=config.COLORS['bg_dark'])
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # LEFT: Display Area
        left_frame = Frame(main_container, bg=config.COLORS['bg_medium'], bd=2, relief=SOLID)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0,5))
        
        # Image counter
        self.image_counter_label = Label(
            left_frame,
            text="📸 Chưa có ảnh",
            font=("Arial", 11, "bold"),
            bg=config.COLORS['bg_medium'],
            fg=config.COLORS['accent_green']
        )
        self.image_counter_label.pack(pady=5)
        
        # Canvas hiển thị
        self.canvas = Canvas(
            left_frame, 
            bg=config.COLORS['bg_dark'], 
            width=config.CANVAS_WIDTH, 
            height=config.CANVAS_HEIGHT
        )
        self.canvas.pack(padx=10, pady=5)
        
        # Navigation buttons
        nav_frame = Frame(left_frame, bg=config.COLORS['bg_medium'])
        nav_frame.pack(pady=5)
        
        self.btn_prev = Button(
            nav_frame,
            text="⬅️ TRƯỚC",
            bg=config.COLORS['text_gray'],
            fg='white',
            font=('Arial', 10, 'bold'),
            width=12,
            command=self.prev_image,
            state=DISABLED,
            cursor='hand2',
            bd=0
        )
        self.btn_prev.pack(side=LEFT, padx=5)
        
        self.btn_next = Button(
            nav_frame,
            text="SAU ➡️",
            bg=config.COLORS['text_gray'],
            fg='white',
            font=('Arial', 10, 'bold'),
            width=12,
            command=self.next_image,
            state=DISABLED,
            cursor='hand2',
            bd=0
        )
        self.btn_next.pack(side=LEFT, padx=5)
        
        # Control buttons
        control_frame = Frame(left_frame, bg=config.COLORS['bg_medium'])
        control_frame.pack(pady=10)
        
        btn_style = {
            'font': ('Arial', 11, 'bold'),
            'width': 15,
            'height': 2,
            'bd': 0,
            'cursor': 'hand2'
        }
        
        self.btn_upload = Button(
            control_frame,
            text="📁 UPLOAD ẢNH",
            bg=config.COLORS['accent_purple'],
            fg='white',
            command=self.upload_images,
            **btn_style
        )
        self.btn_upload.grid(row=0, column=0, padx=5)
        
        self.btn_camera = Button(
            control_frame,
            text="📷 BẬT CAMERA",
            bg=config.COLORS['accent_blue'],
            fg='white',
            command=self.toggle_camera,
            **btn_style
        )
        self.btn_camera.grid(row=0, column=1, padx=5)
        
        self.btn_detect = Button(
            control_frame,
            text="⚡ DETECT",
            bg=config.COLORS['accent_red'],
            fg='white',
            command=self.detect_food,
            **btn_style
        )
        self.btn_detect.grid(row=0, column=2, padx=5)
        
        self.btn_reset = Button(
            control_frame,
            text="🔄 RESET",
            bg=config.COLORS['text_gray'],
            fg='white',
            command=self.reset,
            **btn_style
        )
        self.btn_reset.grid(row=0, column=3, padx=5)
        
        # MIDDLE: Settings & Current Results
        middle_frame = Frame(main_container, bg=config.COLORS['bg_medium'], width=300, bd=2, relief=SOLID)
        middle_frame.pack(side=LEFT, fill=Y, padx=5)
        middle_frame.pack_propagate(False)
        
        # Settings Panel
        settings_label = Label(
            middle_frame,
            text="⚙️ CÀI ĐẶT",
            font=("Arial", 14, "bold"),
            bg=config.COLORS['bg_medium'],
            fg=config.COLORS['accent_green']
        )
        settings_label.pack(pady=10)
        
        # Confidence slider
        conf_frame = Frame(middle_frame, bg=config.COLORS['bg_medium'])
        conf_frame.pack(pady=10, padx=20, fill=X)
        
        self.conf_label = Label(
            conf_frame,
            text=f"Confidence: {self.confidence_threshold}",
            font=("Arial", 10),
            bg=config.COLORS['bg_medium'],
            fg='white'
        )
        self.conf_label.pack()
        
        self.confidence_slider = Scale(
            conf_frame,
            from_=config.MIN_CONFIDENCE,
            to=config.MAX_CONFIDENCE,
            resolution=0.05,
            orient=HORIZONTAL,
            bg=config.COLORS['bg_medium'],
            fg='white',
            troughcolor=config.COLORS['bg_dark'],
            highlightthickness=0,
            command=self.update_confidence
        )
        self.confidence_slider.set(self.confidence_threshold)
        self.confidence_slider.pack(fill=X)
        
        # Results Panel
        results_label = Label(
            middle_frame,
            text="📊 KẾT QUẢ HIỆN TẠI",
            font=("Arial", 14, "bold"),
            bg=config.COLORS['bg_medium'],
            fg=config.COLORS['accent_green']
        )
        results_label.pack(pady=(20,10))
        
        # Scrollable results
        results_container = Frame(middle_frame, bg=config.COLORS['bg_dark'])
        results_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = Scrollbar(results_container)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.results_text = Text(
            results_container,
            bg=config.COLORS['bg_dark'],
            fg='white',
            font=('Courier New', 9),
            yscrollcommand=scrollbar.set,
            wrap=WORD,
            bd=0,
            padx=10,
            pady=10
        )
        self.results_text.pack(fill=BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)
        
        # RIGHT: History Panel
        right_frame = Frame(main_container, bg=config.COLORS['bg_medium'], width=400, bd=2, relief=SOLID)
        right_frame.pack(side=RIGHT, fill=Y, padx=(5,0))
        right_frame.pack_propagate(False)
        
        # History Header
        history_header = Frame(right_frame, bg=config.COLORS['bg_medium'])
        history_header.pack(fill=X, pady=10, padx=10)
        
        Label(
            history_header,
            text="📜 LỊCH SỬ NHẬN DIỆN",
            font=("Arial", 14, "bold"),
            bg=config.COLORS['bg_medium'],
            fg=config.COLORS['accent_green']
        ).pack(side=LEFT)
        
        Button(
            history_header,
            text="💾",
            bg=config.COLORS['accent_blue'],
            fg='white',
            font=('Arial', 10, 'bold'),
            width=3,
            command=self.export_history,
            cursor='hand2',
            bd=0
        ).pack(side=RIGHT, padx=5)
        
        Button(
            history_header,
            text="🗑️",
            bg=config.COLORS['accent_orange'],
            fg='white',
            font=('Arial', 10, 'bold'),
            width=3,
            command=self.clear_history,
            cursor='hand2',
            bd=0
        ).pack(side=RIGHT)
        
        # Stats
        stats_frame = Frame(right_frame, bg=config.COLORS['bg_dark'])
        stats_frame.pack(fill=X, padx=10, pady=5)
        
        self.stats_label = Label(
            stats_frame,
            text=f"📊 Tổng: {self.history_manager.get_total_records()} lần detect",
            font=("Arial", 9),
            bg=config.COLORS['bg_dark'],
            fg=config.COLORS['accent_green'],
            anchor=W,
            padx=5,
            pady=5
        )
        self.stats_label.pack(fill=X)
        
        # History List
        history_container = Frame(right_frame, bg=config.COLORS['bg_dark'])
        history_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        history_scrollbar = Scrollbar(history_container)
        history_scrollbar.pack(side=RIGHT, fill=Y)
        
        self.history_text = Text(
            history_container,
            bg=config.COLORS['bg_dark'],
            fg='white',
            font=('Courier New', 8),
            yscrollcommand=history_scrollbar.set,
            wrap=WORD,
            bd=0,
            padx=5,
            pady=5
        )
        self.history_text.pack(fill=BOTH, expand=True)
        history_scrollbar.config(command=self.history_text.yview)
        
        self.update_history_display()
        
        # Status bar
        self.status_label = Label(
            self.main_frame,
            text="✅ Ready! Upload nhiều ảnh để detect",
            font=("Arial", 10),
            bg=config.COLORS['bg_header'],
            fg=config.COLORS['accent_green'],
            anchor=W
        )
        self.status_label.pack(side=BOTTOM, fill=X)
    
    def create_loading_screen(self):
        """Tạo màn hình loading"""
        self.loading_frame = Frame(self.container, bg=config.COLORS['bg_dark'])
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Main container
        main_container = Frame(self.loading_frame, bg=config.COLORS['bg_dark'])
        main_container.pack(expand=True, fill=BOTH)
        
        # Title
        title_label = Label(
            main_container,
            text="🍕 FOOD DETECTION AI",
            font=("Arial", 28, "bold"),
            bg=config.COLORS['bg_dark'],
            fg=config.COLORS['accent_green']
        )
        title_label.pack(pady=40)
        
        # Loading canvas
        self.loading_canvas = Canvas(
            main_container,
            width=200,
            height=200,
            bg=config.COLORS['bg_dark'],
            highlightthickness=0
        )
        self.loading_canvas.pack(pady=20)
        
        # Message
        self.loading_message_label = Label(
            main_container,
            text="Đang xử lý...",
            font=("Arial", 16),
            bg=config.COLORS['bg_dark'],
            fg=config.COLORS['text_white']
        )
        self.loading_message_label.pack(pady=20)
        
        # Progress text
        self.loading_progress_label = Label(
            main_container,
            text="⚡ Đang phân tích hình ảnh...",
            font=("Arial", 12),
            bg=config.COLORS['bg_dark'],
            fg=config.COLORS['accent_purple']
        )
        self.loading_progress_label.pack(pady=10)
    
    def create_result_screen(self):
        """Tạo màn hình kết quả (trang trong cùng cửa sổ)"""
        self.result_frame = Frame(self.container, bg=config.COLORS['bg_dark'])
        self.result_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Header: Trở về + tiêu đề + Hủy kết quả
        header_frame = Frame(self.result_frame, bg=config.COLORS['bg_header'], height=80)
        header_frame.pack(fill=X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        btn_back = Button(
            header_frame,
            text="← Trở về",
            bg=config.COLORS['accent_blue'],
            fg='white',
            font=('Arial', 10, 'bold'),
            command=lambda: self.show_screen("main"),
            cursor='hand2',
            bd=0,
            padx=20,
            pady=10
        )
        btn_back.pack(side=LEFT, padx=10)
        
        title_label = Label(
            header_frame,
            text="📊 Kết quả nhận diện",
            font=("Arial", 20, "bold"),
            bg=config.COLORS['bg_header'],
            fg=config.COLORS['accent_green']
        )
        title_label.pack(side=LEFT, expand=True)
        
        btn_cancel_result = Button(
            header_frame,
            text="🗑️ Hủy kết quả nhận diện này",
            bg=config.COLORS['accent_orange'],
            fg='white',
            font=('Arial', 10, 'bold'),
            cursor='hand2',
            bd=0,
            padx=16,
            pady=10,
            command=self.cancel_result
        )
        btn_cancel_result.pack(side=RIGHT, padx=10)
        
        # Main container với canvas + scrollbar
        main_container = Frame(self.result_frame, bg=config.COLORS['bg_dark'])
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        self.result_canvas = Canvas(main_container, bg=config.COLORS['bg_dark'], highlightthickness=0)
        scrollbar = Scrollbar(main_container, orient="vertical", command=self.result_canvas.yview)
        self.result_scrollable_frame = Frame(self.result_canvas, bg=config.COLORS['bg_dark'])
        
        self.result_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all"))
        )
        self.result_canvas_window = self.result_canvas.create_window((0, 0), window=self.result_scrollable_frame, anchor="nw")
        self.result_canvas.configure(yscrollcommand=scrollbar.set)
        self.result_canvas.bind("<Configure>", self._on_result_canvas_configure)
        self.result_canvas.bind("<MouseWheel>", lambda ev: self.result_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units"))
        
        self.result_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def _on_result_canvas_configure(self, event):
        """Cập nhật width frame bên trong canvas khi resize"""
        self.result_canvas.itemconfig(self.result_canvas_window, width=event.width)

    def cancel_result(self):
        """Hủy kết quả nhận diện hiện tại và về trang chính"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn hủy kết quả nhận diện này?"):
            self.current_detections = []
            self.show_screen("main")
            self.status_label.config(text="✅ Đã hủy kết quả. Bạn có thể detect lại.")

    # Nội dung QR: chuỗi ngắn (17 ký tự) → QR version 1, rất ít ô, mọi máy quét được
    PAYMENT_QR_TEXT = "THANHTOANTHANHCON"

    def _make_qr_image(self, data, size=200):
        """Tạo ảnh QR (PIL) từ chuỗi. Trả về ImageTk hoặc None nếu không có thư viện."""
        if not HAS_QR:
            return None
        # version=1 cố định nếu data ngắn → QR 21x21 ô, to và rõ; box_size lớn = dễ quét
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        try:
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        except AttributeError:
            img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def show_payment_dialog(self):
        """Hiện hộp thoại thanh toán: chọn hình thức -> hiện QR (nếu có) -> xác nhận -> xuất hóa đơn."""
        total = getattr(self, '_result_total_price', 0)
        total_cal = getattr(self, '_result_total_calories', 0)
        pay_win = Toplevel(self.root)
        self._payment_window = pay_win
        pay_win.title("💳 Thanh toán")
        pay_w, pay_h = 500, 780
        pay_win.geometry(f"{pay_w}x{pay_h}")
        def _on_close():
            self._payment_window = None
            pay_win.destroy()
        pay_win.protocol("WM_DELETE_WINDOW", _on_close)
        pay_win.configure(bg=config.COLORS['bg_dark'])
        pay_win.transient(self.root)
        pay_win.resizable(False, False)
        pay_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (pay_w // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (pay_h // 2)
        pay_win.geometry(f"+{max(0, x)}+{max(0, y)}")

        # Tổng tiền
        f_top = Frame(pay_win, bg=config.COLORS['bg_header'], padx=16, pady=12)
        f_top.pack(fill=X)
        Label(f_top, text="💳 THANH TOÁN HÓA ĐƠN", font=("Arial", 14, "bold"),
              bg=config.COLORS['bg_header'], fg=config.COLORS['accent_green']).pack(anchor=W)
        Label(f_top, text=f"💰 Tổng tiền: {total:,} VNĐ", font=("Arial", 12, "bold"),
              bg=config.COLORS['bg_header'], fg=config.COLORS['accent_orange']).pack(anchor=W, pady=4)
        Label(f_top, text=f"🔥 Tổng calo: {total_cal:,} kcal", font=("Arial", 10),
              bg=config.COLORS['bg_header'], fg='white').pack(anchor=W)

        method_var = StringVar(value="cash")
        methods = [
            ("cash", "💵 Tiền mặt (thanh toán khi nhận)"),
            ("momo", "📱 Momo"),
            ("zalopay", "📱 ZaloPay"),
            ("vietqr", "🏦 VietQR (quét mã chuyển khoản)"),
        ]
        f_method = LabelFrame(pay_win, text="Chọn hình thức thanh toán", bg=config.COLORS['bg_medium'],
                              fg=config.COLORS['accent_green'], font=("Arial", 10, "bold"), padx=10, pady=8)
        f_method.pack(fill=X, padx=16, pady=10)
        for val, label in methods:
            Radiobutton(
                f_method, text=label, variable=method_var, value=val,
                bg=config.COLORS['bg_medium'], fg='white', selectcolor=config.COLORS['bg_dark'],
                activebackground=config.COLORS['bg_medium'], font=("Arial", 10),
                command=lambda: None
            ).pack(anchor=W, pady=4)

        # Vùng hiển thị QR
        f_qr = Frame(pay_win, bg=config.COLORS['bg_dark'], pady=12)
        f_qr.pack(fill=X)
        qr_label = Label(f_qr, text="Chọn hình thức thanh toán để hiển thị mã QR",
                         font=("Arial", 10), bg=config.COLORS['bg_dark'], fg=config.COLORS['text_gray'])
        qr_label.pack(pady=8)
        qr_photo_holder = [None]

        def update_qr():
            m = method_var.get()
            qr_label.config(text="Chọn hình thức thanh toán để hiển thị mã QR")
            for w in f_qr.winfo_children():
                if w != qr_label:
                    w.destroy()
            if m == "cash":
                qr_label.config(text="💵 Thanh toán khi nhận hàng. Không cần quét mã.")
                return
            # QR chứa link web: điện thoại mở link → trang "Thanh toán thành công" → app tự xuất hóa đơn
            if self._payment_server_url:
                qr_content = f"{self._payment_server_url}?m={m}"
            else:
                qr_content = self.PAYMENT_QR_TEXT
            if HAS_QR:
                photo = self._make_qr_image(qr_content, size=400)
                if photo:
                    qr_photo_holder[0] = photo
                    lab = Label(f_qr, image=photo, bg="white", padx=12, pady=12)
                    lab.pack(pady=6)
                if self._payment_server_url:
                    qr_label.config(
                        text="Quét mã QR bằng điện thoại (cùng Wi‑Fi với máy tính).\n"
                             "Trình duyệt mở trang 'Thanh toán thành công' → App tự xuất hóa đơn.\n"
                             "Hoặc bấm 'Xác nhận đã thanh toán' bên dưới để xuất ngay."
                    )
                else:
                    qr_label.config(
                        text="Quét mã QR (mã chữ). Hoặc bấm 'Xác nhận đã thanh toán' để xuất hóa đơn."
                    )
            else:
                qr_label.config(text="Cài: pip install qrcode[pil] để hiện QR.")

        method_var.trace_add("write", lambda *a: update_qr())
        update_qr()

        def on_confirm():
            method = method_var.get()
            name_map = {"cash": "Tiền mặt", "momo": "Momo", "zalopay": "ZaloPay", "vietqr": "VietQR"}
            path = self.save_invoice_to_downloads(name_map.get(method, method))
            self._payment_window = None
            pay_win.destroy()
            messagebox.showinfo("Thanh toán thành công", f"Đã thanh toán bằng {name_map.get(method, method)}.\n\nHóa đơn đã lưu:\n{path}")
        
        Button(pay_win, text="✅ XÁC NHẬN ĐÃ THANH TOÁN", bg=config.COLORS['accent_green'], fg='white',
               font=('Arial', 11, 'bold'), width=28, height=2, bd=0, cursor='hand2', command=on_confirm).pack(pady=16)
        Button(pay_win, text="Đóng", bg=config.COLORS['text_gray'], fg='white', font=('Arial', 10),
               bd=0, padx=20, pady=6, cursor='hand2', command=_on_close).pack(pady=0)

    def save_invoice_to_downloads(self, payment_method_name):
        """Tạo nội dung hóa đơn và lưu vào thư mục Downloads. Trả về đường dẫn file."""
        total = getattr(self, '_result_total_price', 0)
        total_cal = getattr(self, '_result_total_calories', 0)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        downloads = Path.home() / "Downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        path = downloads / f"HoaDon_Food_{ts}.txt"
        lines = [
            "=" * 50,
            "        🍕 HÓA ĐƠN THANH TOÁN - FOOD DETECTION",
            "=" * 50,
            "",
            f"Ngày: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"Mã HĐ: INV_{ts}",
            "",
            "-" * 50,
            f"{'Tên món':<32} {'Giá':>10} {'Calo':>8}",
            "-" * 50,
        ]
        for det in self.current_detections:
            key = self.normalize_food_key(det['name'])
            info = self.food_data.get(key, {})
            name = (info.get('name_vi') or det['name'])[:30]
            price = info.get('price', 0)
            cal = info.get('calories', 0)
            lines.append(f"{name:<32} {price:>9,}đ {cal:>7} kcal")
        lines.extend([
            "-" * 50,
            "",
            f"🍽️  Tổng số món: {len(self.current_detections)}",
            f"🔥 Tổng calo: {total_cal:,} kcal",
            "",
            f"💰 TỔNG TIỀN: {total:,} VNĐ",
            f"💳 Thanh toán: {payment_method_name}",
            "",
            "=" * 50,
            "      Cảm ơn quý khách! Hẹn gặp lại 🎉",
            "=" * 50,
        ])
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    def show_screen(self, screen_name):
        """Chuyển đổi giữa các màn hình"""
        self.current_screen = screen_name
        
        # Ẩn tất cả
        self.main_frame.place_forget()
        self.loading_frame.place_forget()
        self.result_frame.place_forget()
        
        # Hiện màn hình được chọn
        if screen_name == "main":
            self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.is_loading_active = False
            self.update_result_button_visibility()
        elif screen_name == "loading":
            self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.is_loading_active = True
            self.animate_spinner()
        elif screen_name == "result":
            self.result_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.display_result_screen()
    
    def animate_spinner(self):
        """Animate loading spinner"""
        if not self.is_loading_active or self.current_screen != "loading":
            return
        
        self.loading_canvas.delete("all")
        
        # Vẽ spinner
        center_x, center_y = 100, 100
        radius = 50
        num_dots = 8
        
        for i in range(num_dots):
            angle = (self.loading_angle + i * 45) % 360
            rad = math.radians(angle)
            
            x = center_x + radius * math.cos(rad)
            y = center_y + radius * math.sin(rad)
            
            # Màu sắc khác nhau tùy theo vị trí
            intensity = int(255 * (i + 1) / num_dots)
            color = f'#{intensity:02x}{intensity//2:02x}88'
            
            self.loading_canvas.create_oval(x-8, y-8, x+8, y+8, fill=color, outline=color)
        
        self.loading_angle = (self.loading_angle + 10) % 360
        self.root.after(50, self.animate_spinner)
    
    def update_confidence(self, value):
        """Update confidence threshold"""
        self.confidence_threshold = float(value)
        self.conf_label.config(text=f"Confidence: {self.confidence_threshold:.2f}")
    
    def upload_images(self):
        """Upload NHIỀU ảnh cùng lúc"""
        file_paths = filedialog.askopenfilenames(
            title="Chọn nhiều ảnh",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if not file_paths:
            return
        
        # Clear previous uploads
        self.uploaded_images = []
        self.current_index = 0
        
        # Load all images
        for path in file_paths:
            img = load_image(path)
            if img is not None:
                self.uploaded_images.append({
                    'path': path,
                    'image': img,
                    'detected_image': None,
                    'results': None
                })
        
        if len(self.uploaded_images) > 0:
            self.current_index = 0
            self.display_current_image()
            self.update_navigation()
            self.status_label.config(text=f"📁 Đã load {len(self.uploaded_images)} ảnh")
        else:
            messagebox.showerror("Lỗi", "Không thể load ảnh nào!")
    
    def prev_image(self):
        """Chuyển về ảnh trước"""
        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_image()
            self.update_navigation()
    
    def next_image(self):
        """Chuyển sang ảnh sau"""
        if self.current_index < len(self.uploaded_images) - 1:
            self.current_index += 1
            self.display_current_image()
            self.update_navigation()
    
    def display_current_image(self):
        """Hiển thị ảnh hiện tại"""
        if len(self.uploaded_images) == 0:
            return
        
        current = self.uploaded_images[self.current_index]
        
        # Ưu tiên hiển thị ảnh đã detect
        if current['detected_image'] is not None:
            self.display_image(current['detected_image'])
            if current['results'] is not None:
                self.show_results(current['results'])
        else:
            self.display_image(current['image'])
            self.results_text.delete(1.0, END)
            self.results_text.insert(END, "⚠️ Chưa detect ảnh này\n\n")
            self.results_text.insert(END, "Nhấn nút DETECT để nhận diện")
        
        # Update counter
        self.image_counter_label.config(
            text=f"📸 Ảnh {self.current_index + 1}/{len(self.uploaded_images)}: {Path(current['path']).name}"
        )
    
    def update_navigation(self):
        """Cập nhật trạng thái nút điều hướng"""
        if len(self.uploaded_images) <= 1:
            self.btn_prev.config(state=DISABLED)
            self.btn_next.config(state=DISABLED)
        else:
            self.btn_prev.config(state=NORMAL if self.current_index > 0 else DISABLED)
            self.btn_next.config(state=NORMAL if self.current_index < len(self.uploaded_images) - 1 else DISABLED)
    
    def toggle_camera(self):
        """Bật/tắt camera"""
        if not self.is_camera_running:
            self.uploaded_images = []
            self.current_index = 0
            self.update_navigation()
            self.image_counter_label.config(text="📷 Camera Mode")
            
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
                self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
                
                self.is_camera_running = True
                self.btn_camera.config(text="⏸️ TẮT CAMERA", bg=config.COLORS['accent_orange'])
                self.status_label.config(text="📷 Camera đang chạy...")
                self.update_camera()
            else:
                self.status_label.config(text="❌ Không thể mở camera!")
        else:
            self.stop_camera()
    
    def stop_camera(self):
        """Dừng camera"""
        self.is_camera_running = False
        if self.cap:
            self.cap.release()
        self.btn_camera.config(text="📷 BẬT CAMERA", bg=config.COLORS['accent_blue'])
        self.status_label.config(text="⏸️ Camera đã tắt")
        self.image_counter_label.config(text="📸 Chưa có ảnh")
    
    def update_camera(self):
        """Update camera frame"""
        if self.is_camera_running:
            ret, frame = self.cap.read()
            if ret:
                self.current_image = frame
                self.display_image(frame)
            self.root.after(30, self.update_camera)
    
    def detect_food(self):
        """Chạy detection với loading screen"""
        if not self.model_manager.is_loaded():
            self.status_label.config(text="❌ Model chưa được load!")
            return
        
        # Camera mode
        if self.is_camera_running and self.current_image is not None:
            self.detect_with_loading([self.current_image], is_camera=True)
            return
        
        # Multi-image mode
        if len(self.uploaded_images) == 0:
            self.status_label.config(text="⚠️ Chưa có ảnh để detect!")
            return
        
        # Collect images to detect
        images_to_detect = []
        for img_data in self.uploaded_images:
            if img_data['detected_image'] is None:
                images_to_detect.append(img_data)
        
        if len(images_to_detect) == 0:
            messagebox.showinfo("Thông báo", "Tất cả ảnh đã được detect!")
            return
        
        # Run detection với loading
        self.detect_with_loading(images_to_detect, is_camera=False)
    
    def detect_with_loading(self, items, is_camera=False):
        """
        Chạy detection với màn hình loading
        
        Args:
            items: List ảnh cần detect hoặc single image (camera)
            is_camera: True nếu là camera mode
        """
        # Chuyển sang loading screen
        self.show_screen("loading")
        self.loading_message_label.config(text="Đang xử lý...")
        self.loading_progress_label.config(text="⚡ Đang phân tích hình ảnh...")
        
        # Run detection trong thread
        def run_detection():
            try:
                if is_camera:
                    # Camera mode - single image
                    img = items[0]
                    self.root.after(0, lambda: self.loading_progress_label.config(text="⚡ Đang nhận diện..."))
                    
                    result = self.model_manager.detect(img, self.confidence_threshold)
                    if result:
                        annotated_frame = result.plot()
                        
                        # Collect detections
                        detections = []
                        for box in result.boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            class_name = result.names[cls_id]
                            detections.append({
                                "name": class_name,
                                "confidence": conf
                            })
                        
                        # Update UI
                        self.current_detections = detections
                        self.root.after(0, lambda: self.display_image(annotated_frame))
                        self.root.after(0, lambda: self.show_results(result))
                        self.root.after(0, lambda: self.history_manager.add_record(detections, "camera"))
                        self.root.after(0, lambda: self.update_history_display())
                        self.root.after(0, lambda: self.status_label.config(text=f"✅ Phát hiện {len(result.boxes)} món ăn!"))
                        
                        # Go to result screen
                        if len(detections) > 0:
                            self.root.after(500, lambda: self.show_result_screen())
                        else:
                            self.root.after(500, lambda: self.show_screen("main"))
                
                else:
                    # Multi-image mode
                    total = len(items)
                    all_detections = []
                    
                    for i, img_data in enumerate(items):
                        self.root.after(0, lambda idx=i, t=total: 
                                      self.loading_message_label.config(text=f"Đang xử lý ảnh {idx+1}/{t}..."))
                        self.root.after(0, lambda: 
                                      self.loading_progress_label.config(text=f"⚡ {Path(items[i]['path']).name}"))
                        
                        result = self.model_manager.detect(img_data['image'], self.confidence_threshold)
                        if result:
                            annotated_frame = result.plot()
                            img_data['detected_image'] = annotated_frame
                            img_data['results'] = result
                            
                            # Collect detections
                            detections = []
                            for box in result.boxes:
                                cls_id = int(box.cls[0])
                                conf = float(box.conf[0])
                                class_name = result.names[cls_id]
                                detections.append({
                                    "name": class_name,
                                    "confidence": conf
                                })
                            
                            all_detections.extend(detections)
                            
                            # Add to history
                            self.root.after(0, lambda d=detections, p=img_data['path']: 
                                          self.history_manager.add_record(d, f"upload ({Path(p).name})"))
                    
                    # Update UI
                    self.root.after(0, self.update_history_display)
                    self.root.after(0, lambda: self.status_label.config(text=f"✅ Đã detect {len(items)} ảnh!"))
                    
                    # Set current detections and go to result screen
                    self.current_detections = all_detections
                    if len(all_detections) > 0:
                        self.root.after(500, lambda: self.show_result_screen())
                    else:
                        self.root.after(500, lambda: self.show_screen("main"))
            
            except Exception as e:
                print(f"❌ Lỗi detection: {e}")
                self.root.after(0, lambda: self.show_screen("main"))
                self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Lỗi khi detect:\n{e}"))
        
        # Start detection thread
        thread = threading.Thread(target=run_detection, daemon=True)
        thread.start()
    
    def normalize_food_key(self, class_name):
        """Chuẩn hóa tên class từ model để khớp với key trong food_data
        Ví dụ: 'Banh-canh' -> 'Banh_canh'
        """
        # Thử các biến thể khác nhau theo thứ tự ưu tiên
        variations = [
            class_name,  # Trực tiếp (ví dụ: 'Pho')
            class_name.replace('-', '_'),  # Thay gạch ngang bằng gạch dưới (ví dụ: 'Banh-canh' -> 'Banh_canh')
            class_name.replace('_', '-'),  # Thay gạch dưới bằng gạch ngang
            class_name.replace(' ', '_'),  # Thay space bằng gạch dưới
            class_name.replace('-', ''),  # Loại bỏ gạch ngang
            class_name.replace('_', ''),  # Loại bỏ gạch dưới
        ]
        
        # Thêm biến thể với Bun_ và Banh_ nếu có 'Bun-' hoặc 'Banh-'
        if class_name.startswith('Bun-'):
            variations.append('Bun_' + class_name[4:].replace('-', '_'))
        elif class_name.startswith('Banh-'):
            variations.append('Banh_' + class_name[5:].replace('-', '_'))
        
        for key in variations:
            if key in self.food_data:
                print(f"✅ Normalized '{class_name}' -> '{key}'")
                return key
        
        print(f"⚠️ Không normalize được '{class_name}'")
        return class_name
    
    def display_result_screen(self):
        """Hiển thị chi tiết kết quả detection"""
        # Clear previous content
        for widget in self.result_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Debug: in ra danh sách detections
        print(f"\n=== DEBUG: Total detections: {len(self.current_detections)} ===")
        for i, det in enumerate(self.current_detections):
            print(f"  {i+1}. {det['name']} (confidence: {det['confidence']:.2%})")
        print("=" * 50 + "\n")
        
        if not self.current_detections:
            label = Label(
                self.result_scrollable_frame,
                text="❌ Không phát hiện món ăn nào!",
                font=("Arial", 14),
                bg=config.COLORS['bg_dark'],
                fg=config.COLORS['accent_red']
            )
            label.pack(pady=20)
            return
        
        # Calculate totals (lưu để dùng cho thanh toán)
        total_price = 0
        total_calories = 0
        self._result_total_price = 0
        self._result_total_calories = 0
        
        # Display each food item
        displayed_count = 0  # Đếm số món được hiển thị
        for detection in self.current_detections:
            class_name = detection['name']
            confidence = detection['confidence']
            
            # Chuẩn hóa tên class để khớp với food_data
            food_key = self.normalize_food_key(class_name)
            
            # Get food info
            food_info = self.food_data.get(food_key, {})
            
            # Nếu không tìm thấy, tạo fallback data
            if not food_info:
                print(f"⚠️ Không tìm thấy thông tin cho: {class_name}")
                food_info = {
                    'name_vi': class_name,
                    'price': 0,
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'description': f'Phát hiện: {class_name}'
                }
            
            displayed_count += 1
            
            # Add to totals
            p = food_info.get('price', 0)
            c = food_info.get('calories', 0)
            total_price += p
            total_calories += c
            self._result_total_price += p
            self._result_total_calories += c
            
            # Create food frame
            food_frame = Frame(
                self.result_scrollable_frame,
                bg=config.COLORS['bg_medium'],
                bd=2,
                relief=SOLID
            )
            food_frame.pack(fill=X, padx=10, pady=10)
            
            # Header với số thứ tự và tên món
            header_frame = Frame(food_frame, bg=config.COLORS['bg_header'])
            header_frame.pack(fill=X, padx=10, pady=10)
            
            Label(
                header_frame,
                text=f"#{displayed_count} {food_info.get('name_vi', food_key)}",
                font=("Arial", 14, "bold"),
                bg=config.COLORS['bg_header'],
                fg=config.COLORS['accent_green']
            ).pack(side=LEFT)
            
            Label(
                header_frame,
                text=f"Confidence: {confidence:.1%}",
                font=("Arial", 10),
                bg=config.COLORS['bg_header'],
                fg='white'
            ).pack(side=RIGHT)
            
            # Content frame
            content_frame = Frame(food_frame, bg=config.COLORS['bg_dark'])
            content_frame.pack(fill=X, padx=10, pady=10)
            
            # Description
            description = food_info.get('description', 'Không có mô tả')
            desc_label = Label(
                content_frame,
                text=f"📝 {description}",
                font=("Arial", 10),
                bg=config.COLORS['bg_dark'],
                fg='white',
                wraplength=600,
                justify=LEFT
            )
            desc_label.pack(anchor=W, pady=5)
            
            # Nutrition info (left side)
            left_frame = Frame(content_frame, bg=config.COLORS['bg_dark'])
            left_frame.pack(side=LEFT, fill=BOTH, expand=True)
            
            nutrition_frame = Frame(left_frame, bg=config.COLORS['bg_dark'])
            nutrition_frame.pack(fill=X, pady=5)
            
            nutrition_data = [
                (f"💰 Giá: {food_info.get('price', 0):,} VNĐ", config.COLORS['accent_green']),
                (f"🔥 Calo: {food_info.get('calories', 0)} kcal", config.COLORS['accent_red']),
                (f"🥩 Protein: {food_info.get('protein', 0)}g", config.COLORS['accent_blue']),
                (f"🍚 Carbs: {food_info.get('carbs', 0)}g", config.COLORS['accent_purple']),
                (f"🥛 Fat: {food_info.get('fat', 0)}g", config.COLORS['accent_orange']),
            ]
            
            for text, color in nutrition_data:
                Label(
                    nutrition_frame,
                    text=text,
                    font=("Arial", 9),
                    bg=config.COLORS['bg_dark'],
                    fg=color
                ).pack(anchor=W)
            
            # Nutrition chart (right side)
            right_frame = Frame(content_frame, bg=config.COLORS['bg_dark'])
            right_frame.pack(side=RIGHT, padx=10)
            
            self.draw_nutrition_chart(
                right_frame,
                food_info.get('protein', 0),
                food_info.get('carbs', 0),
                food_info.get('fat', 0)
            )
        
        # Summary frame
        summary_frame = Frame(
            self.result_scrollable_frame,
            bg=config.COLORS['bg_header'],
            bd=2,
            relief=SOLID
        )
        summary_frame.pack(fill=X, padx=10, pady=10)
        
        Label(
            summary_frame,
            text="📊 TỔNG KẾT",
            font=("Arial", 14, "bold"),
            bg=config.COLORS['bg_header'],
            fg=config.COLORS['accent_green']
        ).pack(pady=10)
        
        summary_data = [
            f"🍽️  Tổng số món: {len(self.current_detections)}",
            f"💰 Tổng giá tiền: {total_price:,} VNĐ",
            f"🔥 Tổng calo: {total_calories} kcal"
        ]
        
        for text in summary_data:
            Label(
                summary_frame,
                text=text,
                font=("Arial", 11),
                bg=config.COLORS['bg_header'],
                fg='white'
            ).pack(anchor=W, padx=20, pady=5)
        
        # Nút Thanh toán
        btn_pay_frame = Frame(self.result_scrollable_frame, bg=config.COLORS['bg_dark'])
        btn_pay_frame.pack(fill=X, padx=10, pady=16)
        Button(
            btn_pay_frame,
            text="💳 THANH TOÁN",
            bg=config.COLORS['accent_green'],
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2,
            bd=0,
            cursor='hand2',
            command=self.show_payment_dialog
        ).pack(pady=8)
    
    def show_results(self, result):
        """Hiển thị kết quả detection trong panel"""
        self.results_text.delete(1.0, END)
        
        if len(result.boxes) == 0:
            self.results_text.insert(END, "❌ Không phát hiện món ăn nào!\n\n")
            self.results_text.insert(END, "💡 Thử:\n")
            self.results_text.insert(END, "  • Giảm confidence threshold\n")
            self.results_text.insert(END, "  • Chọn ảnh rõ hơn\n")
            return
        
        self.results_text.insert(END, f"🎯 Phát hiện: {len(result.boxes)} món\n")
        self.results_text.insert(END, "="*35 + "\n\n")
        
        for i, box in enumerate(result.boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = result.names[cls_id]
            
            self.results_text.insert(END, f"#{i+1} {class_name}\n")
            self.results_text.insert(END, f"   Confidence: {conf:.2%}\n")
            
            bar_length = int(conf * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            self.results_text.insert(END, f"   [{bar}]\n\n")
    
    def update_history_display(self):
        """Cập nhật hiển thị lịch sử"""
        self.history_text.delete(1.0, END)
        self.stats_label.config(text=f"📊 Tổng: {self.history_manager.get_total_records()} lần detect")
        
        history = self.history_manager.get_history()
        
        if len(history) == 0:
            self.history_text.insert(END, "📭 Chưa có lịch sử\n\n")
            self.history_text.insert(END, "Bắt đầu detect để\nlưu lịch sử!")
            return
        
        for record in history:
            source_icon = "📷" if "camera" in record["source"] else "📁"
            self.history_text.insert(END, f"{source_icon} {record['timestamp']}\n")
            self.history_text.insert(END, f"   Nguồn: {record['source']}\n")
            self.history_text.insert(END, f"   Phát hiện: {record['total_detected']} món\n")
            
            for item in record["items"][:3]:
                self.history_text.insert(END, f"   • {item['name']} ({item['confidence']:.0%})\n")
            
            if record["total_detected"] > 3:
                self.history_text.insert(END, f"   ... và {record['total_detected'] - 3} món khác\n")
            
            self.history_text.insert(END, "-"*40 + "\n\n")
    
    def clear_history(self):
        """Xóa toàn bộ lịch sử"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa toàn bộ lịch sử?"):
            self.history_manager.clear_history()
            self.update_history_display()
            self.status_label.config(text="🗑️ Đã xóa lịch sử")
    
    def export_history(self):
        """Xuất lịch sử ra file JSON"""
        if self.history_manager.get_total_records() == 0:
            messagebox.showwarning("Cảnh báo", "Chưa có lịch sử để xuất!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"food_detection_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if file_path:
            if self.history_manager.export_history(file_path):
                messagebox.showinfo(
                    "Thành công", 
                    f"Đã xuất {self.history_manager.get_total_records()} bản ghi!\n\n{file_path}"
                )
                self.status_label.config(text=f"💾 Đã xuất lịch sử: {Path(file_path).name}")
            else:
                messagebox.showerror("Lỗi", "Không thể xuất file!")
                self.status_label.config(text="❌ Lỗi xuất file!")
    
    def display_image(self, img):
        """Hiển thị ảnh lên canvas"""
        img_tk, new_w, new_h = resize_image_to_canvas(
            img, 
            config.CANVAS_WIDTH, 
            config.CANVAS_HEIGHT
        )
        
        self.canvas.delete("all")
        self.canvas.create_image(
            config.CANVAS_WIDTH//2,
            config.CANVAS_HEIGHT//2,
            image=img_tk,
            anchor=CENTER
        )
        self.canvas.image = img_tk
    
    def draw_nutrition_chart(self, parent, protein, carbs, fat):
        """
        Vẽ biểu đồ tròn dinh dưỡng (Donut chart)
        
        Args:
            parent: Frame chứa biểu đồ
            protein: Lượng protein (g)
            carbs: Lượng carbs (g)
            fat: Lượng chất béo (g)
        """
        canvas = Canvas(
            parent, 
            width=160, 
            height=165, 
            bg=config.COLORS['bg_dark'], 
            highlightthickness=0
        )
        canvas.pack()
        
        # Tổng
        total = protein + carbs + fat
        if total == 0:
            total = 1  # Tránh chia 0
        
        # Màu sắc
        colors = ['#FF6B6B', '#4ECDC4', '#FFE66D']  # Protein, Carbs, Fat
        labels = ['P', 'C', 'F']  # Ký tự viết tắt
        values = [protein, carbs, fat]
        
        center_x, center_y = 75, 75
        radius = 50
        inner_radius = 30
        
        start_angle = 0
        
        # Vẽ từng phần của donut chart
        for i, (value, color, label) in enumerate(zip(values, colors, labels)):
            if value > 0:
                extent = (value / total) * 360
                
                # Vẽ arc (phần ngoài)
                canvas.create_arc(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    start=start_angle,
                    extent=extent,
                    fill=color,
                    outline='white',
                    width=1
                )
                
                # Tính toán vị trí nhãn (ở giữa của arc)
                mid_angle = start_angle + extent / 2
                label_rad = math.radians(mid_angle)
                label_radius = (radius + inner_radius) / 2
                label_x = center_x + label_radius * math.cos(label_rad)
                label_y = center_y + label_radius * math.sin(label_rad)
                
                # Vẽ nhãn ở giữa arc
                canvas.create_text(
                    label_x, label_y,
                    text=f"{value}g",
                    fill='white',
                    font=('Arial', 8, 'bold'),
                    anchor=CENTER
                )
                
                start_angle += extent
        
        # Vẽ vòng tròn trắng ở giữa (tạo donut effect)
        canvas.create_oval(
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius,
            fill=config.COLORS['bg_dark'],
            outline=''
        )
        
        # Legend ghi rõ chỉ số: Protein/Carbs/Fat kèm số (g)
        legend_y = 118
        legend_items = [
            (f'Protein: {protein}g', colors[0]),
            (f'Carbs: {carbs}g', colors[1]),
            (f'Fat: {fat}g', colors[2])
        ]
        for i, (text, color) in enumerate(legend_items):
            canvas.create_rectangle(10, legend_y + i*14, 20, legend_y + i*14 + 10, fill=color, outline='white')
            canvas.create_text(26, legend_y + i*14 + 5, text=text, anchor=W, fill='white', font=('Arial', 8, 'bold'))
    
    def reset(self):
        """Reset về trạng thái ban đầu"""
        self.stop_camera()
        self.current_image = None
        self.uploaded_images = []
        self.current_index = 0
        self.canvas.delete("all")
        self.results_text.delete(1.0, END)
        self.image_counter_label.config(text="📸 Chưa có ảnh")
        self.update_navigation()
        self.status_label.config(text="✅ Ready! Upload nhiều ảnh để detect")
    
    def update_result_button_visibility(self):
        """Hiện/ẩn nút Xem kết quả trên trang chính theo current_detections"""
        if hasattr(self, 'btn_see_result') and self.btn_see_result.winfo_exists():
            if self.current_detections:
                self.btn_see_result.place(relx=1.0, rely=0.5, anchor=E, x=-10)
            else:
                self.btn_see_result.place_forget()

    def show_result_screen(self):
        """Chuyển sang trang kết quả (cùng cửa sổ, không mở Toplevel)"""
        if self.current_detections:
            self.show_screen("result")
        self.update_result_button_visibility()
    
    def __del__(self):
        """Cleanup khi đóng app"""
        if self.cap:
            self.cap.release()
