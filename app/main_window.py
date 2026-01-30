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
from cart_manager import CartManager
from payment_handler import PaymentHandler

try:
    import qrcode
    from PIL import Image, ImageTk
    HAS_QR = True
except ImportError:
    HAS_QR = False



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
        
        # Cart manager
        self.cart_manager = CartManager()
        
        # Payment handler
        self.payment_handler = PaymentHandler(
            root=self.root,
            cart_manager=self.cart_manager,
            get_cart_totals_func=self._get_cart_totals,
            normalize_food_key_func=self.normalize_food_key,
            food_data=self.food_data
        )
        
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

        # Cart & session (mỗi lần detect = 1 phiên giao dịch)
        # cart: gom tất cả detections thành giỏ hàng {food_key: {..., quantity, max_quantity, ...}}
        self.cart = {}
        self.current_session = None
        
        # Payment state
        self._last_payment_method = None
        self._last_invoice_path = None
        
        # Screen states
        self.current_screen = "main"  # "main", "loading", "result", "payment", "payment_success"
        
        # Frames
        self.main_frame = None
        self.loading_frame = None
        self.result_frame = None
        self.payment_frame = None
        self.payment_success_frame = None
        
        # Store for animation
        self.loading_angle = 0
        self.is_loading_active = False
        
        # Payment: server link + cửa sổ thanh toán (để đóng khi web xác nhận)
        self.payment_handler.start_payment_server(self)
        
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
    
    
    def on_payment_success_from_web(self, method):
        """Gọi từ server khi điện thoại mở link thanh toán → chuyển sang màn hình thành công."""
        name_map = {"cash": "Tiền mặt", "momo": "Momo", "zalopay": "ZaloPay", "vietqr": "VietQR"}
        method_name = name_map.get(method, method)
        if getattr(self, "cart", None):
            if self.current_session:
                self.current_session["status"] = "paid"
            # Lưu thông tin thanh toán để hiển thị
            self._last_payment_method = method_name
            self._last_invoice_path = None  # Chưa xuất hóa đơn
            # Chuyển sang màn hình thành công
            self.show_screen("payment_success")
        else:
            messagebox.showwarning("Cảnh báo", "Chưa có đơn hàng để thanh toán.")
    
    def setup_ui(self):
        """Thiết kế giao diện chính"""
        # Container chính
        self.container = Frame(self.root, bg=config.COLORS['bg_dark'])
        self.container.pack(fill=BOTH, expand=True)
        
        # Tạo các frame cho mỗi screen
        self.create_main_screen()
        self.create_loading_screen()
        self.create_result_screen()
        self.create_payment_screen()
        self.create_payment_success_screen()
        
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

    def create_payment_screen(self):
        """Tạo màn hình thanh toán (trang trong cùng cửa sổ)"""
        self.payment_frame = Frame(self.container, bg=config.COLORS['bg_dark'])
        self.payment_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Header: Trở về + tiêu đề
        header_frame = Frame(self.payment_frame, bg=config.COLORS['bg_header'], height=80)
        header_frame.pack(fill=X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        btn_back = Button(
            header_frame,
            text="← Hủy thanh toán",
            bg=config.COLORS['accent_red'],
            fg='white',
            font=('Arial', 10, 'bold'),
            command=lambda: self.show_screen("result"),
            cursor='hand2',
            bd=0,
            padx=20,
            pady=10
        )
        btn_back.pack(side=LEFT, padx=10)
        
        title_label = Label(
            header_frame,
            text="💳 Thanh toán",
            font=("Arial", 20, "bold"),
            bg=config.COLORS['bg_header'],
            fg=config.COLORS['accent_green']
        )
        title_label.pack(side=LEFT, expand=True)
        
        # Main container với scroll
        main_container = Frame(self.payment_frame, bg=config.COLORS['bg_dark'])
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        payment_canvas = Canvas(main_container, bg=config.COLORS['bg_dark'], highlightthickness=0)
        payment_scrollbar = Scrollbar(main_container, orient="vertical", command=payment_canvas.yview)
        payment_scrollable_frame = Frame(payment_canvas, bg=config.COLORS['bg_dark'])
        
        payment_scrollable_frame.bind(
            "<Configure>",
            lambda e: payment_canvas.configure(scrollregion=payment_canvas.bbox("all"))
        )
        payment_canvas_window = payment_canvas.create_window((0, 0), window=payment_scrollable_frame, anchor="nw")
        payment_canvas.configure(yscrollcommand=payment_scrollbar.set)
        payment_canvas.bind("<Configure>", lambda e: payment_canvas.itemconfig(payment_canvas_window, width=e.width))
        payment_canvas.bind("<MouseWheel>", lambda ev: payment_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units"))
        
        payment_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        payment_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Lưu reference để có thể update sau
        self.payment_scrollable_frame = payment_scrollable_frame
        self.payment_canvas = payment_canvas
    
    def create_payment_success_screen(self):
        """Tạo màn hình thanh toán thành công với hóa đơn"""
        self.payment_success_frame = Frame(self.container, bg=config.COLORS['bg_dark'])
        self.payment_success_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Header
        header_frame = Frame(self.payment_success_frame, bg=config.COLORS['bg_header'], height=80)
        header_frame.pack(fill=X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        title_label = Label(
            header_frame,
            text="✅ Thanh toán thành công",
            font=("Arial", 20, "bold"),
            bg=config.COLORS['bg_header'],
            fg=config.COLORS['accent_green']
        )
        title_label.pack(expand=True)
        
        # Main container với scroll
        main_container = Frame(self.payment_success_frame, bg=config.COLORS['bg_dark'])
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        success_canvas = Canvas(main_container, bg=config.COLORS['bg_dark'], highlightthickness=0)
        success_scrollbar = Scrollbar(main_container, orient="vertical", command=success_canvas.yview)
        success_scrollable_frame = Frame(success_canvas, bg=config.COLORS['bg_dark'])
        
        success_scrollable_frame.bind(
            "<Configure>",
            lambda e: success_canvas.configure(scrollregion=success_canvas.bbox("all"))
        )
        success_canvas_window = success_canvas.create_window((0, 0), window=success_scrollable_frame, anchor="nw")
        success_canvas.configure(yscrollcommand=success_scrollbar.set)
        success_canvas.bind("<Configure>", lambda e: success_canvas.itemconfig(success_canvas_window, width=e.width))
        success_canvas.bind("<MouseWheel>", lambda ev: success_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units"))
        
        success_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        success_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Lưu reference
        self.payment_success_scrollable_frame = success_scrollable_frame

    def show_payment_dialog(self):
        """Chuyển sang màn hình thanh toán"""
        # Validate giỏ hàng trước khi cho phép thanh toán
        if not self._validate_cart_before_payment():
            return
        self.show_screen("payment")
        self.display_payment_screen()

    def show_screen(self, screen_name):
        """Chuyển đổi giữa các màn hình"""
        self.current_screen = screen_name
        
        # Ẩn tất cả
        self.main_frame.place_forget()
        self.loading_frame.place_forget()
        self.result_frame.place_forget()
        if self.payment_frame:
            self.payment_frame.place_forget()
        if self.payment_success_frame:
            self.payment_success_frame.place_forget()
        
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
        elif screen_name == "payment":
            self.payment_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.display_payment_screen()
        elif screen_name == "payment_success":
            self.payment_success_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.display_payment_success_screen()
    
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

        # Khởi tạo session mới cho lần detect này
        self.current_session = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "status": "unpaid",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        # Xoá cart & detections cũ
        self.cart = {}
        self.current_detections = []
        
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
                        self.build_cart_from_detections()
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
                    self.build_cart_from_detections()
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
        """Chuẩn hóa tên class từ model để khớp với key trong food_data"""
        return CartManager.normalize_food_key(class_name, self.food_data)

    # ===================== CART / SESSION =====================
    
    def build_cart_from_detections(self):
        """
        Gom current_detections thành giỏ hàng (cart) theo food_key.
        Đây là bước khởi tạo CartItems từ DetectedItems (read‑only).
        """
        self.cart = CartManager.build_cart_from_detections(
            self.current_detections, 
            self.food_data, 
            self.normalize_food_key
        )
        self._recalc_cart_totals()
    
    def _get_cart_totals(self):
        """
        Trả về (total_items, total_price, total_calories) từ cart,
        chỉ tính các món chưa bị excluded_from_payment.
        """
        return CartManager.get_cart_totals(self.cart)
    
    def _recalc_cart_totals(self):
        """Cập nhật lại tổng tiền / calo dựa trên cart hiện tại."""
        _, total_price, total_calories = self._get_cart_totals()
        self._result_total_price = total_price
        self._result_total_calories = total_calories

    def _validate_cart_before_payment(self):
        """Kiểm tra chênh lệch giữa DetectedItems và CartItems trước khi thanh toán."""
        return CartManager.validate_cart_before_payment(self.cart)

    def _can_edit_cart(self):
        """Chỉ cho chỉnh giỏ khi session đang ở trạng thái unpaid."""
        return CartManager.can_edit_cart(self.current_session)

    def _change_cart_quantity(self, key, delta):
        """Tăng/giảm quantity trong cart có kiểm soát."""
        if CartManager.change_cart_quantity(self.cart, key, delta, self.current_session):
            self._recalc_cart_totals()
            # Render lại màn hình kết quả
            if self.current_screen == "result":
                self.display_result_screen()
    
    def _delete_cart_item(self, key):
        """Đánh dấu món là excluded_from_payment."""
        if CartManager.toggle_exclude_item(self.cart, key, self.current_session):
            # Set excluded = True (không toggle)
            if key in self.cart:
                self.cart[key]["excluded"] = True
            self._recalc_cart_totals()
            if self.current_screen == "result":
                self.display_result_screen()
    
    def _toggle_exclude_item(self, key):
        """Bật/tắt trạng thái excluded_from_payment cho một món trong cart."""
        if CartManager.toggle_exclude_item(self.cart, key, self.current_session):
            self._recalc_cart_totals()
            if self.current_screen == "result":
                self.display_result_screen()
    
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
        
        # Summary frame (dựa trên CART)
        total_items, total_price_cart, total_calories_cart = self._get_cart_totals()
        summary_frame = Frame(
            self.result_scrollable_frame,
            bg=config.COLORS['bg_header'],
            bd=2,
            relief=SOLID
        )
        summary_frame.pack(fill=X, padx=10, pady=10)
        
        Label(
            summary_frame,
            text="📊 TỔNG KẾT (GIỎ HÀNG)",
            font=("Arial", 14, "bold"),
            bg=config.COLORS['bg_header'],
            fg=config.COLORS['accent_green']
        ).pack(pady=10)
        
        summary_data = [
            f"🍽️  Tổng số phần: {total_items}",
            f"💰 Tổng giá tiền: {total_price_cart:,} VNĐ",
            f"🔥 Tổng calo: {total_calories_cart} kcal"
        ]
        
        for text in summary_data:
            Label(
                summary_frame,
                text=text,
                font=("Arial", 11),
                bg=config.COLORS['bg_header'],
                fg='white'
            ).pack(anchor=W, padx=20, pady=5)

        # CART TABLE: cho phép chỉnh sửa có ràng buộc theo workflow
        if self.cart:
            cart_frame = Frame(self.result_scrollable_frame, bg=config.COLORS['bg_dark'])
            cart_frame.pack(fill=X, padx=10, pady=(0, 16))

            header = Frame(cart_frame, bg=config.COLORS['bg_dark'])
            header.pack(fill=X, pady=(0, 4))
            cols = ["Món ăn", "SL", "Giá", "Thành tiền", "Conf", "Hành động"]
            widths = [30, 5, 10, 18, 8, 14]
            for i, (c, w) in enumerate(zip(cols, widths)):
                Label(
                    header,
                    text=c,
                    font=("Arial", 10, "bold"),
                    bg=config.COLORS['bg_dark'],
                    fg=config.COLORS['accent_green'],
                    width=w,
                    anchor=W
                ).grid(row=0, column=i, padx=4)

            for row_idx, item in enumerate(self.cart.values(), start=1):
                row = Frame(cart_frame, bg=config.COLORS['bg_medium'])
                row.pack(fill=X, pady=2)

                name = item["name_vi"]
                qty = int(item["quantity"])
                price = item["price"]
                total_line = price * qty
                conf = item.get("avg_conf", 0)
                detected_qty = int(item.get("detected_qty", 0))
                excluded = bool(item.get("excluded", False))
                can_decrease = qty > detected_qty

                Label(row, text=name, font=("Arial", 10), bg=config.COLORS['bg_medium'], fg='white',
                      width=30, anchor=W).grid(row=0, column=0, padx=4, pady=2, sticky=W)

                qty_frame = Frame(row, bg=config.COLORS['bg_medium'])
                qty_frame.grid(row=0, column=1, padx=4)
                btn_minus = Button(
                    qty_frame,
                    text="-",
                    width=2,
                    bd=0,
                    cursor="hand2",
                    state=(NORMAL if can_decrease else DISABLED),
                    command=lambda k=item["key"]: self._change_cart_quantity(k, -1),
                )
                btn_minus.pack(side=LEFT)
                Label(qty_frame, text=str(qty), width=3, bg=config.COLORS['bg_medium'],
                      fg='white').pack(side=LEFT)
                Button(qty_frame, text="+", width=2, bd=0, cursor="hand2",
                       command=lambda k=item["key"]: self._change_cart_quantity(k, +1)).pack(side=LEFT)

                Label(row, text=f"{price:,}đ", font=("Arial", 10), bg=config.COLORS['bg_medium'],
                      fg=config.COLORS['accent_orange'], width=10, anchor=E).grid(row=0, column=2, padx=4)

                total_text = f"{total_line:,}đ"
                total_fg = config.COLORS['accent_green']
                if excluded:
                    total_text += " (Không thanh toán)"
                    total_fg = config.COLORS['text_gray']
                Label(
                    row,
                    text=total_text,
                    font=("Arial", 10, "bold"),
                    bg=config.COLORS['bg_medium'],
                    fg=total_fg,
                    width=18,
                    anchor=E,
                ).grid(row=0, column=3, padx=4)

                Label(row, text=f"{conf:.0%}", font=("Arial", 10), bg=config.COLORS['bg_medium'],
                      fg='white', width=8, anchor=E).grid(row=0, column=4, padx=4)

                # Nút bỏ/khôi phục khỏi thanh toán (không xóa khỏi dữ liệu nhận diện)
                exclude_label = "Bỏ khỏi TT" if not excluded else "Khôi phục"
                Button(
                    row,
                    text=exclude_label,
                    bg=config.COLORS['accent_orange'],
                    fg='white',
                    font=('Arial', 9, 'bold'),
                    bd=0,
                    cursor='hand2',
                    command=lambda k=item["key"]: self._toggle_exclude_item(k)
                ).grid(row=0, column=5, padx=4)
        
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
    
    def display_payment_screen(self):
        """Hiển thị màn hình thanh toán"""
        # Clear previous content
        for widget in self.payment_scrollable_frame.winfo_children():
            widget.destroy()
        
        total = getattr(self, '_result_total_price', 0)
        total_cal = getattr(self, '_result_total_calories', 0)
        
        # Tổng tiền
        f_top = Frame(self.payment_scrollable_frame, bg=config.COLORS['bg_header'], padx=16, pady=12)
        f_top.pack(fill=X, padx=10, pady=10)
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
        f_method = LabelFrame(self.payment_scrollable_frame, text="Chọn hình thức thanh toán", 
                              bg=config.COLORS['bg_medium'],
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
        f_qr = Frame(self.payment_scrollable_frame, bg=config.COLORS['bg_dark'], pady=12)
        f_qr.pack(fill=X, padx=16)
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
            # QR chứa link web
            payment_server_url = getattr(self.payment_handler, '_payment_server_url', None)
            if payment_server_url:
                qr_content = f"{payment_server_url}?m={m}"
            else:
                qr_content = "THANHTOANTHANHCON"
            
            try:
                import qrcode
                from PIL import Image, ImageTk
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(qr_content)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                try:
                    img = img.resize((400, 400), Image.Resampling.LANCZOS)
                except AttributeError:
                    img = img.resize((400, 400), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                qr_photo_holder[0] = photo
                lab = Label(f_qr, image=photo, bg="white", padx=12, pady=12)
                lab.pack(pady=6)
                if payment_server_url:
                    qr_label.config(
                        text="Quét mã QR bằng điện thoại (cùng Wi‑Fi với máy tính).\n"
                             "Trình duyệt mở trang 'Thanh toán thành công' → App tự chuyển màn hình.\n"
                             "Hoặc bấm 'Xác nhận đã thanh toán' bên dưới để tiếp tục."
                    )
                else:
                    qr_label.config(
                        text="Quét mã QR (mã chữ). Hoặc bấm 'Xác nhận đã thanh toán' để tiếp tục."
                    )
            except ImportError:
                qr_label.config(text="Cài: pip install qrcode[pil] để hiện QR.")
        
        method_var.trace_add("write", lambda *a: update_qr())
        update_qr()
        
        def on_confirm():
            method = method_var.get()
            name_map = {"cash": "Tiền mặt", "momo": "Momo", "zalopay": "ZaloPay", "vietqr": "VietQR"}
            method_name = name_map.get(method, method)
            if self.current_session:
                self.current_session["status"] = "paid"
            # Lưu thông tin thanh toán
            self._last_payment_method = method_name
            self._last_invoice_path = None  # Chưa xuất hóa đơn
            # Chuyển sang màn hình thành công
            self.show_screen("payment_success")
        
        btn_frame = Frame(self.payment_scrollable_frame, bg=config.COLORS['bg_dark'])
        btn_frame.pack(fill=X, padx=16, pady=16)
        Button(btn_frame, text="✅ XÁC NHẬN ĐÃ THANH TOÁN", bg=config.COLORS['accent_green'], fg='white',
               font=('Arial', 11, 'bold'), width=28, height=2, bd=0, cursor='hand2', command=on_confirm).pack(pady=8)
    
    def display_payment_success_screen(self):
        """Hiển thị màn hình thanh toán thành công với hóa đơn"""
        # Clear previous content
        for widget in self.payment_success_scrollable_frame.winfo_children():
            widget.destroy()
        
        payment_method = getattr(self, '_last_payment_method', 'Tiền mặt')
        invoice_path = getattr(self, '_last_invoice_path', None)
        
        # Header thành công
        success_header = Frame(self.payment_success_scrollable_frame, bg=config.COLORS['bg_header'], padx=20, pady=20)
        success_header.pack(fill=X, padx=10, pady=10)
        
        Label(success_header, text="✅ THANH TOÁN THÀNH CÔNG", 
              font=("Arial", 18, "bold"), bg=config.COLORS['bg_header'], 
              fg=config.COLORS['accent_green']).pack(pady=10)
        Label(success_header, text=f"Phương thức: {payment_method}", 
              font=("Arial", 12), bg=config.COLORS['bg_header'], fg='white').pack()
        
        # Hiển thị hóa đơn
        invoice_frame = Frame(self.payment_success_scrollable_frame, bg='white', padx=20, pady=20)
        invoice_frame.pack(fill=X, padx=20, pady=10)
        
        # Tạo nội dung hóa đơn đẹp như siêu thị
        invoice_text = self._generate_invoice_text()
        
        invoice_label = Label(
            invoice_frame,
            text=invoice_text,
            font=("Courier New", 10),
            bg='white',
            fg='black',
            justify=LEFT,
            anchor=NW
        )
        invoice_label.pack(fill=BOTH, expand=True)
        
        # Nút hành động
        action_frame = Frame(self.payment_success_scrollable_frame, bg=config.COLORS['bg_dark'], padx=20, pady=20)
        action_frame.pack(fill=X, padx=10, pady=10)
        
        def export_invoice():
            """Xuất hóa đơn và reset session"""
            path = self.payment_handler.save_invoice_to_downloads(
                self.cart, self.current_detections, payment_method
            )
            self._last_invoice_path = path
            messagebox.showinfo("Thành công", f"Đã xuất hóa đơn:\n{path}")
            # Reset session sau khi xuất hóa đơn thành công
            self._end_session()
        
        def skip_invoice():
            """Không xuất hóa đơn, kết thúc phiên"""
            # Reset session sau khi không xuất hóa đơn
            self._end_session()
        
        Button(action_frame, text="📄 XUẤT HÓA ĐƠN", bg=config.COLORS['accent_green'], fg='white',
               font=('Arial', 11, 'bold'), width=20, height=2, bd=0, cursor='hand2', 
               command=export_invoice).pack(side=LEFT, padx=10, pady=10)
        Button(action_frame, text="❌ KHÔNG XUẤT HÓA ĐƠN", bg=config.COLORS['accent_red'], fg='white',
               font=('Arial', 11, 'bold'), width=20, height=2, bd=0, cursor='hand2', 
               command=skip_invoice).pack(side=RIGHT, padx=10, pady=10)
    
    def _generate_invoice_text(self):
        """Tạo nội dung hóa đơn đẹp như siêu thị"""
        total_items, total_price, total_cal = self._get_cart_totals()
        payment_method = getattr(self, '_last_payment_method', 'Tiền mặt')
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        lines = []
        lines.append(" " * 20 + "🍕 FOOD DETECTION AI")
        lines.append(" " * 18 + "=" * 30)
        lines.append(" " * 20 + "HÓA ĐƠN BÁN HÀNG")
        lines.append(" " * 18 + "=" * 30)
        lines.append("")
        lines.append(f"Ngày: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append(f"Mã HĐ: INV_{ts}")
        lines.append(f"Phương thức: {payment_method}")
        lines.append("-" * 50)
        lines.append(f"{'Tên món':<25} {'SL':>3} {'Giá':>12} {'TT':>12}")
        lines.append("-" * 50)
        
        for item in self.cart.values():
            qty = int(item.get("quantity", 0))
            if item.get("excluded") or qty <= 0:
                continue
            name = (item.get("name_vi") or item.get("key"))[:23]
            price = item.get("price", 0)
            total_line = price * qty
            lines.append(f"{name:<25} {qty:>3} {price:>11,}đ {total_line:>11,}đ")
        
        lines.append("-" * 50)
        lines.append(f"{'Tổng số phần:':<25} {total_items:>3}")
        lines.append(f"{'Tổng calo:':<25} {total_cal:,} kcal")
        lines.append("")
        lines.append(f"{'TỔNG TIỀN:':<25} {total_price:>11,}đ")
        lines.append("")
        lines.append(" " * 15 + "Cảm ơn quý khách!")
        lines.append(" " * 12 + "Hẹn gặp lại 🎉")
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
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
        self.current_detections = []
        self.cart = {}
        self.current_session = None
        self.update_result_button_visibility()

    def _end_session(self):
        """
        Kết thúc một phiên giao dịch và reset về trạng thái ban đầu:
        - Giữ lịch sử detection (detection_history.json) để báo cáo.
        - Reset tất cả: cart, detections, uploaded images, camera, UI.
        - Đưa UI về trạng thái sẵn sàng cho phiên mới (như chưa detect gì).
        """
        # Dừng camera nếu đang chạy
        self.stop_camera()
        
        # Reset images và camera state
        self.current_image = None
        self.uploaded_images = []
        self.current_index = 0
        
        # Reset cart và detections
        self.cart = {}
        self.current_detections = []
        self.current_session = None
        
        # Reset payment state
        self._last_payment_method = None
        self._last_invoice_path = None
        
        # Reset UI elements
        if hasattr(self, 'canvas'):
            self.canvas.delete("all")
        if hasattr(self, 'results_text'):
            self.results_text.delete(1.0, END)
        if hasattr(self, 'image_counter_label'):
            self.image_counter_label.config(text="📸 Chưa có ảnh")
        if hasattr(self, 'update_navigation'):
            self.update_navigation()
        
        # Reset UI và chuyển về màn hình chính
        self.update_result_button_visibility()
        self.show_screen("main")
        self.status_label.config(text="✅ Đã kết thúc phiên. Sẵn sàng cho lần detect mới.")
    
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
