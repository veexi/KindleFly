import os
import sys
import threading
import queue
import webbrowser
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

# KindleFly modules
from config_manager import ConfigManager
from history_manager import HistoryManager
from service import KindleService
from email_sender import EmailSender

# Thread-safe queue for logging from background service to Tkinter GUI
log_queue = queue.Queue()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class KindleFlyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Initialize Managers
        # If compiled with PyInstaller, use application path or user data
        self.app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.config_manager = ConfigManager(self.app_dir)
        self.history_manager = HistoryManager(self.app_dir)

        # 2. Window Settings
        self.title("KindleFly - 电子书自动推送服务")
        self.geometry("980x640")
        self.minsize(900, 580)
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 3. App Assets (Loaded from extracted temp folder if packaged)
        self.icon_png_path = resource_path(os.path.join("assets", "app_icon.png"))
        self.icon_ico_path = resource_path(os.path.join("assets", "app_icon.ico"))
        
        # Load window icon
        if os.path.exists(self.icon_ico_path):
            self.iconbitmap(self.icon_ico_path)
            
        if os.path.exists(self.icon_png_path):
            self.logo_image = ctk.CTkImage(
                light_image=Image.open(self.icon_png_path),
                dark_image=Image.open(self.icon_png_path),
                size=(50, 50)
            )
        else:
            self.logo_image = None

        # 4. Service Initialization
        self.service = KindleService(
            config_manager=self.config_manager,
            history_manager=self.history_manager,
            log_callback=self.queue_log,
            status_callback=self.on_service_status_changed
        )

        # 5. Tray Icon variables
        self.tray_icon = None
        self.tray_thread = None

        # 6. Layout Grid Configurations
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 7. Build UI Components
        self.create_sidebar()
        
        # Navigation container (Right Panel)
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Create Views
        self.views = {}
        self.create_dashboard_view()
        self.create_smtp_view()
        self.create_kindle_folder_view()
        self.create_history_view()

        # Default Tab
        self.select_tab("dashboard")

        # 8. Start Log Poller
        self.poll_logs()

        # 9. Bind window close event and startup actions
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Start System Tray in background thread
        self.start_tray_icon()
        
        # Auto start service if configured
        if self.config_manager.get("auto_start_service"):
            self.after(1000, self.start_service)
        else:
            # Update GUI state toStopped
            self.on_service_status_changed(False)

    # ----------------------------------------------------
    # Logging Thread-safe Helper
    # ----------------------------------------------------
    def queue_log(self, message, level="info"):
        log_queue.put((message, level))

    def poll_logs(self):
        """Polls log_queue and writes to dashboard console text box."""
        try:
            while True:
                msg, level = log_queue.get_nowait()
                if "dashboard" in self.views and hasattr(self, "log_textbox"):
                    self.log_textbox.configure(state="normal")
                    self.log_textbox.insert("end", msg + "\n", level)
                    self.log_textbox.configure(state="disabled")
                    self.log_textbox.see("end")
                log_queue.task_done()
        except queue.Empty:
            pass
        self.after(100, self.poll_logs)

    # ----------------------------------------------------
    # Sidebar Builder
    # ----------------------------------------------------
    def create_sidebar(self):
        sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.grid_rowconfigure(5, weight=1) # Spacer

        # Logo and Title
        logo_container = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        logo_container.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        if self.logo_image:
            logo_label = ctk.CTkLabel(logo_container, image=self.logo_image, text="")
            logo_label.grid(row=0, column=0, padx=(0, 10))
            
        title_frame = ctk.CTkFrame(logo_container, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="w")
        
        title_label = ctk.CTkLabel(title_frame, text="KindleFly", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w")
        sub_label = ctk.CTkLabel(title_frame, text="自动推送服务", font=ctk.CTkFont(size=11), text_color="gray")
        sub_label.grid(row=1, column=0, sticky="w")

        # Sidebar Buttons
        self.sidebar_buttons = {}
        
        self.sidebar_buttons["dashboard"] = ctk.CTkButton(
            sidebar_frame, text="📊 控制面板", anchor="w", height=40,
            command=lambda: self.select_tab("dashboard")
        )
        self.sidebar_buttons["dashboard"].grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.sidebar_buttons["smtp"] = ctk.CTkButton(
            sidebar_frame, text="📧 Gmail 发信配置", anchor="w", height=40,
            command=lambda: self.select_tab("smtp")
        )
        self.sidebar_buttons["smtp"].grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.sidebar_buttons["kindle_folder"] = ctk.CTkButton(
            sidebar_frame, text="⚙ 目录 & 接收端", anchor="w", height=40,
            command=lambda: self.select_tab("kindle_folder")
        )
        self.sidebar_buttons["kindle_folder"].grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.sidebar_buttons["history"] = ctk.CTkButton(
            sidebar_frame, text="📜 推送历史记录", anchor="w", height=40,
            command=lambda: self.select_tab("history")
        )
        self.sidebar_buttons["history"].grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        # Sidebar Footer (Service Switch)
        footer_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        footer_frame.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        self.service_switch_var = ctk.BooleanVar(value=False)
        self.service_switch = ctk.CTkSwitch(
            footer_frame, text="服务已关闭", variable=self.service_switch_var,
            command=self.toggle_service_via_switch, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.service_switch.grid(row=0, column=0, pady=10, sticky="w")

        # Theme Selector
        theme_label = ctk.CTkLabel(footer_frame, text="界面主题:", font=ctk.CTkFont(size=11), text_color="gray")
        theme_label.grid(row=1, column=0, sticky="w", pady=(5, 2))
        
        self.theme_menu = ctk.CTkOptionMenu(
            footer_frame, values=["Dark", "Light", "System"], height=25,
            command=lambda v: ctk.set_appearance_mode(v.lower())
        )
        self.theme_menu.grid(row=2, column=0, sticky="ew")

    def select_tab(self, name):
        """Shows the selected frame and updates sidebar button highlights."""
        # Highlight button
        for key, btn in self.sidebar_buttons.items():
            if key == name:
                btn.configure(fg_color=("mymedium", "gray25"), text_color=("white", "white"))
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

        # Hide all views, show selected
        for view_name, view_frame in self.views.items():
            view_frame.grid_forget()

        self.views[name].grid(row=0, column=0, sticky="nsew")
        
        # Special action on tab switch
        if name == "history":
            self.refresh_history_table()

    # ----------------------------------------------------
    # TAB 1: Dashboard View Builder
    # ----------------------------------------------------
    def create_dashboard_view(self):
        view = ctk.CTkFrame(self.container, fg_color="transparent")
        self.views["dashboard"] = view

        view.grid_columnconfigure(0, weight=1)
        view.grid_columnconfigure(1, weight=1)
        view.grid_rowconfigure(2, weight=1)

        # Header Title
        header = ctk.CTkLabel(view, text="📊 控制面板", font=ctk.CTkFont(size=22, weight="bold"))
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 15))

        # --- Cards Grid ---
        # Card 1: Service Status Card
        self.card_status = ctk.CTkFrame(view, height=120)
        self.card_status.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.card_status.grid_propagate(False)
        self.card_status.grid_columnconfigure(0, weight=1)
        
        self.status_title = ctk.CTkLabel(self.card_status, text="服务状态", font=ctk.CTkFont(size=12), text_color="gray")
        self.status_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 2))
        
        self.status_val = ctk.CTkLabel(self.card_status, text="已停止", font=ctk.CTkFont(size=20, weight="bold"), text_color="#EC7063")
        self.status_val.grid(row=1, column=0, sticky="w", padx=15, pady=2)
        
        self.status_details = ctk.CTkLabel(self.card_status, text="自动扫描目录未激活", font=ctk.CTkFont(size=11), text_color="gray")
        self.status_details.grid(row=2, column=0, sticky="w", padx=15, pady=2)

        # Card 2: Send Stats Card
        self.card_stats = ctk.CTkFrame(view, height=120)
        self.card_stats.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        self.card_stats.grid_propagate(False)
        self.card_stats.grid_columnconfigure(0, weight=1)
        
        stats_title = ctk.CTkLabel(self.card_stats, text="历史推送数据", font=ctk.CTkFont(size=12), text_color="gray")
        stats_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 2))
        
        self.stats_val = ctk.CTkLabel(self.card_stats, text="0 本", font=ctk.CTkFont(size=20, weight="bold"))
        self.stats_val.grid(row=1, column=0, sticky="w", padx=15, pady=2)
        
        self.stats_details = ctk.CTkLabel(self.card_stats, text="防重复过滤器运行中", font=ctk.CTkFont(size=11), text_color="gray")
        self.stats_details.grid(row=2, column=0, sticky="w", padx=15, pady=2)

        # Update stats initially
        self.update_dashboard_stats()

        # --- Console Log Panel ---
        log_frame = ctk.CTkFrame(view)
        log_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(15, 10), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        log_header = ctk.CTkFrame(log_frame, height=40, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=15, pady=5)
        
        log_title = ctk.CTkLabel(log_header, text="📜 实 时 运行日志", font=ctk.CTkFont(size=13, weight="bold"))
        log_title.pack(side="left")

        # Action Buttons on Console
        self.btn_scan_now = ctk.CTkButton(log_header, text="立即扫描推送", width=120, height=28, command=self.manual_scan_now)
        self.btn_scan_now.pack(side="right", padx=5)

        self.btn_open_folder = ctk.CTkButton(log_header, text="打开本地目录", fg_color="transparent", border_width=1, width=120, height=28, command=self.open_scan_folder)
        self.btn_open_folder.pack(side="right", padx=5)

        # Log Text Box
        self.log_textbox = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.log_textbox.configure(state="disabled")

        # Log Level Text Colors
        self.log_textbox.tag_config("info", foreground="#5DADE2")      # Light Blue
        self.log_textbox.tag_config("success", foreground="#52BE80")   # Green
        self.log_textbox.tag_config("warning", foreground="#F4D03F")   # Yellow
        self.log_textbox.tag_config("error", foreground="#EC7063")     # Red
        self.log_textbox.tag_config("debug", foreground="#A6ACAF")     # Gray

    def update_dashboard_stats(self):
        records = self.history_manager.get_all_records()
        self.stats_val.configure(text=f"{len(records)} 本")
        
        # Calculate last send time
        if records:
            last_send = records[0].get("sent_at", "")
            self.stats_details.configure(text=f"最后推送: {last_send}")
        else:
            self.stats_details.configure(text="无历史推送记录")

    # ----------------------------------------------------
    # TAB 2: SMTP View Builder (Gmail Pre-configured)
    # ----------------------------------------------------
    def create_smtp_view(self):
        view = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.views["smtp"] = view

        view.grid_columnconfigure(0, weight=1)

        # Header Title
        header = ctk.CTkLabel(view, text="📧 Gmail 发信配置", font=ctk.CTkFont(size=22, weight="bold"))
        header.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 15))

        # Gmail Instructions Guide Alert Box
        guide_frame = ctk.CTkFrame(view, border_color="#5DADE2", border_width=1, fg_color="#1E2A38")
        guide_frame.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")
        guide_frame.grid_columnconfigure(0, weight=1)

        guide_title = ctk.CTkLabel(
            guide_frame, text="💡 谷歌邮箱 (Gmail) 安全配置重要指南", 
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#5DADE2"
        )
        guide_title.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 4))

        instructions = (
            "从 2022 年起，谷歌邮箱已彻底关闭【不够安全的应用】直连通道。\n"
            "要让 KindleFly 能够通过您的 Gmail 自动推送书籍，您需要使用谷歌的【应用专用密码】(App Password)：\n\n"
            "1. 登录您的 谷歌账号控制台 (myaccount.google.com)。\n"
            "2. 点击左侧【安全性】(Security) -> 在【如何登录 Google】板块中开启【两步验证】(2-Step Verification)。\n"
            "3. 开启后，在搜索框搜索【应用专用密码】(App Passwords) 并点击进入。\n"
            "4. 输入一个应用别名（例如: KindleFly），点击【创建】。\n"
            "5. 系统会生成一串 16 位的【应用专用密码】（黄框显示，不带空格）。\n"
            "6. 复制该密码并填入下方的【Gmail 应用密码/授权码】框中！"
        )
        guide_text = ctk.CTkLabel(
            guide_frame, text=instructions, font=ctk.CTkFont(size=12), 
            justify="left", text_color="#D5DBDB"
        )
        guide_text.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 12))

        # Tutorial Link Button
        btn_tutorial = ctk.CTkButton(
            guide_frame, text="🌐 点击跳转 谷歌账号安全管理 🔗", fg_color="transparent", 
            border_width=1, border_color="#5DADE2", text_color="#5DADE2",
            height=28, hover_color="#2C3E50", 
            command=lambda: webbrowser.open("https://myaccount.google.com/security")
        )
        btn_tutorial.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 12))

        # --- Form Fields ---
        form_frame = ctk.CTkFrame(view)
        form_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)

        # 1. Gmail Email
        label_email = ctk.CTkLabel(form_frame, text="您的 Gmail 邮箱:")
        label_email.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        self.entry_email = ctk.CTkEntry(form_frame, placeholder_text="example@gmail.com")
        self.entry_email.grid(row=0, column=1, sticky="ew", padx=15, pady=(15, 5))
        self.entry_email.insert(0, self.config_manager.get("sender_email", ""))

        # 2. Gmail App Password
        label_pwd = ctk.CTkLabel(form_frame, text="Gmail 应用专用密码:")
        label_pwd.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        pwd_input_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        pwd_input_frame.grid(row=1, column=1, sticky="ew", padx=15, pady=5)
        pwd_input_frame.grid_columnconfigure(0, weight=1)

        self.entry_pwd = ctk.CTkEntry(pwd_input_frame, show="*")
        self.entry_pwd.grid(row=0, column=0, sticky="ew")
        self.entry_pwd.insert(0, self.config_manager.smtp_password)

        self.btn_show_pwd = ctk.CTkButton(
            pwd_input_frame, text="👁", width=30, height=28, 
            fg_color="transparent", border_width=1, hover_color="#2C3E50",
            command=self.toggle_password_visibility
        )
        self.btn_show_pwd.grid(row=0, column=1, padx=(5, 0))

        # 3. SMTP Server (Locked or editable for advanced users)
        label_server = ctk.CTkLabel(form_frame, text="SMTP 服务器:")
        label_server.grid(row=2, column=0, sticky="w", padx=15, pady=5)
        self.entry_server = ctk.CTkEntry(form_frame)
        self.entry_server.grid(row=2, column=1, sticky="ew", padx=15, pady=5)
        self.entry_server.insert(0, self.config_manager.get("smtp_server", "smtp.gmail.com"))

        # 4. SMTP Port
        label_port = ctk.CTkLabel(form_frame, text="SMTP 端口:")
        label_port.grid(row=3, column=0, sticky="w", padx=15, pady=5)
        self.entry_port = ctk.CTkEntry(form_frame)
        self.entry_port.grid(row=3, column=1, sticky="ew", padx=15, pady=5)
        self.entry_port.insert(0, str(self.config_manager.get("smtp_port", 587)))

        # 5. SSL vs TLS Option
        label_ssl = ctk.CTkLabel(form_frame, text="连接加密协议:")
        label_ssl.grid(row=4, column=0, sticky="w", padx=15, pady=(5, 15))
        
        ssl_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        ssl_frame.grid(row=4, column=1, sticky="w", padx=15, pady=(5, 15))
        
        self.ssl_var = ctk.BooleanVar(value=self.config_manager.get("smtp_use_ssl", False))
        self.radio_tls = ctk.CTkRadioButton(ssl_frame, text="TLS (推荐，端口587)", variable=self.ssl_var, value=False, command=self.on_smtp_protocol_change)
        self.radio_tls.grid(row=0, column=0, padx=(0, 20))
        self.radio_ssl = ctk.CTkRadioButton(ssl_frame, text="SSL (端口465)", variable=self.ssl_var, value=True, command=self.on_smtp_protocol_change)
        self.radio_ssl.grid(row=0, column=1)

        # --- Proxy Settings Box ---
        proxy_frame = ctk.CTkFrame(view)
        proxy_frame.grid(row=3, column=0, padx=10, pady=(15, 5), sticky="ew")
        proxy_frame.grid_columnconfigure(1, weight=1)

        # Title
        proxy_title_lbl = ctk.CTkLabel(proxy_frame, text="🌐 网络代理配置 (可选，解决本地Gmail连接超时问题)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#5DADE2")
        proxy_title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        # Checkbox Enabled
        self.proxy_enabled_var = ctk.BooleanVar(value=self.config_manager.get("proxy_enabled", False))
        self.cb_proxy_enabled = ctk.CTkCheckBox(
            proxy_frame, text="启用自定义代理服务 (支持 Clash 的 SOCKS5 或 HTTP 代理)", 
            variable=self.proxy_enabled_var, command=self.toggle_proxy_fields
        )
        self.cb_proxy_enabled.grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10))

        # Proxy Type
        self.lbl_proxy_type = ctk.CTkLabel(proxy_frame, text="代理协议类型:")
        self.lbl_proxy_type.grid(row=2, column=0, sticky="w", padx=15, pady=5)
        self.menu_proxy_type = ctk.CTkOptionMenu(proxy_frame, values=["SOCKS5", "HTTP"], width=100)
        self.menu_proxy_type.grid(row=2, column=1, sticky="w", padx=15, pady=5)
        self.menu_proxy_type.set(self.config_manager.get("proxy_type", "SOCKS5"))

        # Proxy Server Host
        self.lbl_proxy_host = ctk.CTkLabel(proxy_frame, text="代理服务器地址:")
        self.lbl_proxy_host.grid(row=3, column=0, sticky="w", padx=15, pady=5)
        self.entry_proxy_host = ctk.CTkEntry(proxy_frame, placeholder_text="127.0.0.1")
        self.entry_proxy_host.grid(row=3, column=1, sticky="ew", padx=15, pady=5)
        self.entry_proxy_host.insert(0, self.config_manager.get("proxy_host", "127.0.0.1"))

        # Proxy Server Port
        self.lbl_proxy_port = ctk.CTkLabel(proxy_frame, text="代理端口:")
        self.lbl_proxy_port.grid(row=4, column=0, sticky="w", padx=15, pady=(5, 15))
        self.entry_proxy_port = ctk.CTkEntry(proxy_frame, placeholder_text="7890 (Clash 默认端口)")
        self.entry_proxy_port.grid(row=4, column=1, sticky="ew", padx=15, pady=(5, 15))
        self.entry_proxy_port.insert(0, str(self.config_manager.get("proxy_port", 7890)))

        # Update initial states
        self.toggle_proxy_fields()

        # --- Action Buttons ---
        btn_frame = ctk.CTkFrame(view, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=10, pady=15, sticky="ew")

        btn_save = ctk.CTkButton(btn_frame, text="保存发信配置", width=140, command=self.save_smtp_config)
        btn_save.pack(side="left", padx=5)

        btn_test = ctk.CTkButton(
            btn_frame, text="测试连接", fg_color="transparent", border_width=1, 
            width=120, command=self.test_smtp_connection
        )
        btn_test.pack(side="left", padx=5)

    def on_smtp_protocol_change(self):
        """Automatically pre-fills ports depending on SSL/TLS selection."""
        is_ssl = self.ssl_var.get()
        self.entry_port.delete(0, "end")
        if is_ssl:
            self.entry_port.insert(0, "465")
        else:
            self.entry_port.insert(0, "587")

    def toggle_proxy_fields(self):
        enabled = self.proxy_enabled_var.get()
        state = "normal" if enabled else "disabled"
        self.menu_proxy_type.configure(state=state)
        self.entry_proxy_host.configure(state=state)
        self.entry_proxy_port.configure(state=state)

    def toggle_password_visibility(self):
        if self.entry_pwd.cget("show") == "*":
            self.entry_pwd.configure(show="")
            self.btn_show_pwd.configure(text="🔒")
        else:
            self.entry_pwd.configure(show="*")
            self.btn_show_pwd.configure(text="👁")

    def save_smtp_config(self):
        email = self.entry_email.get().strip()
        pwd = self.entry_pwd.get().strip()
        server = self.entry_server.get().strip()
        port_str = self.entry_port.get().strip()
        use_ssl = self.ssl_var.get()

        if not email or "@" not in email:
            messagebox.showerror("配置错误", "请填写有效的 Gmail 发信邮箱！")
            return

        if not pwd:
            messagebox.showerror("配置错误", "请填写 Gmail 应用密码！")
            return

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("配置错误", "SMTP 端口必须是数字！")
            return

        # Fetch proxy configs
        proxy_enabled = self.proxy_enabled_var.get()
        proxy_type = self.menu_proxy_type.get()
        proxy_host = self.entry_proxy_host.get().strip()
        proxy_port_str = self.entry_proxy_port.get().strip()
        
        try:
            proxy_port = int(proxy_port_str) if proxy_port_str else 7890
        except ValueError:
            messagebox.showerror("配置错误", "代理端口必须是数字！")
            return

        self.config_manager.set("sender_email", email)
        self.config_manager.smtp_password = pwd
        self.config_manager.set("smtp_server", server)
        self.config_manager.set("smtp_port", port)
        self.config_manager.set("smtp_use_ssl", use_ssl)

        # Save proxy
        self.config_manager.set("proxy_enabled", proxy_enabled)
        self.config_manager.set("proxy_type", proxy_type)
        self.config_manager.set("proxy_host", proxy_host)
        self.config_manager.set("proxy_port", proxy_port)

        messagebox.showinfo("成功", "发信与网络代理配置已安全保存！")

    def test_smtp_connection(self):
        """Runs the SMTP connection test in a separate thread so UI does not freeze."""
        email = self.entry_email.get().strip()
        pwd = self.entry_pwd.get().strip()
        server = self.entry_server.get().strip()
        port_str = self.entry_port.get().strip()
        use_ssl = self.ssl_var.get()

        if not email or not pwd or not server or not port_str:
            messagebox.showerror("配置不完整", "请确保已填写 邮箱、应用密码、服务器和端口！")
            return

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字！")
            return

        # Fetch proxy configs
        proxy_enabled = self.proxy_enabled_var.get()
        proxy_type = self.menu_proxy_type.get()
        proxy_host = self.entry_proxy_host.get().strip()
        proxy_port_str = self.entry_proxy_port.get().strip()
        
        try:
            proxy_port = int(proxy_port_str) if proxy_port_str else 7890
        except ValueError:
            messagebox.showerror("错误", "代理端口必须是数字！")
            return

        test_dialog = ctk.CTkInputDialog(text="请稍候，正在与谷歌邮件服务器通信...", title="测试 SMTP 连接")
        # Since ctk dialog is blocking, a thread is better.
        # We can just show a progress visual or disable button and re-enable.
        # Let's show a loading dialog: we will do this by spawning a thread and updating the user on success/fail.
        def thread_target():
            sender = EmailSender(server, port, email, pwd, use_ssl,
                                 proxy_enabled, proxy_type, proxy_host, proxy_port)
            success, msg = sender.test_connection()
            
            # Run UI modifications in main thread via after()
            if success:
                self.after(0, lambda: messagebox.showinfo("测试通过", msg))
            else:
                self.after(0, lambda: messagebox.showerror("连接失败", msg))

        t = threading.Thread(target=thread_target, daemon=True)
        t.start()

    # ----------------------------------------------------
    # TAB 3: Kindle & Folder Settings View Builder
    # ----------------------------------------------------
    def create_kindle_folder_view(self):
        view = ctk.CTkFrame(self.container, fg_color="transparent")
        self.views["kindle_folder"] = view

        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(2, weight=1) # expand

        # Header Title
        header = ctk.CTkLabel(view, text="⚙ 目录与 Kindle 推送配置", font=ctk.CTkFont(size=22, weight="bold"))
        header.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 15))

        # --- Settings Box ---
        form_frame = ctk.CTkFrame(view)
        form_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)

        # 1. Kindle Receive Email
        label_kindle = ctk.CTkLabel(form_frame, text="Kindle 接收端邮箱:")
        label_kindle.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        self.entry_kindle = ctk.CTkEntry(form_frame, placeholder_text="example@kindle.com")
        self.entry_kindle.grid(row=0, column=1, sticky="ew", padx=15, pady=(15, 5))
        self.entry_kindle.insert(0, self.config_manager.get("kindle_email", ""))

        # 2. Local Folder to Scan
        label_folder = ctk.CTkLabel(form_frame, text="自动扫描的本地目录:")
        label_folder.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        folder_picker_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        folder_picker_frame.grid(row=1, column=1, sticky="ew", padx=15, pady=5)
        folder_picker_frame.grid_columnconfigure(0, weight=1)

        self.entry_folder = ctk.CTkEntry(folder_picker_frame, placeholder_text="请选择需要监控的文件夹路径...")
        self.entry_folder.grid(row=0, column=0, sticky="ew")
        self.entry_folder.insert(0, self.config_manager.get("scan_folder", ""))

        btn_browse = ctk.CTkButton(
            folder_picker_frame, text="选择文件夹", width=90, 
            command=self.browse_folder
        )
        btn_browse.grid(row=0, column=1, padx=(5, 0))

        # 3. Scanning Interval (Minutes Slider)
        label_interval = ctk.CTkLabel(form_frame, text="自动扫描间隔时间:")
        label_interval.grid(row=2, column=0, sticky="w", padx=15, pady=5)
        
        slider_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        slider_frame.grid(row=2, column=1, sticky="ew", padx=15, pady=5)
        slider_frame.grid_columnconfigure(0, weight=1)

        self.slider_val = self.config_manager.get("scan_interval_minutes", 10)
        self.slider_label = ctk.CTkLabel(slider_frame, text=f"{self.slider_val} 分钟", width=80)
        self.slider_label.grid(row=0, column=1, padx=5)

        self.slider = ctk.CTkSlider(
            slider_frame, from_=1, to=60, number_of_steps=59,
            command=self.on_slider_change
        )
        self.slider.grid(row=0, column=0, sticky="ew")
        self.slider.set(self.slider_val)

        # 4. Allowed Formats Checklist
        label_formats = ctk.CTkLabel(form_frame, text="需要推送的文件类型:")
        label_formats.grid(row=3, column=0, sticky="w", padx=15, pady=(5, 15))

        checklist_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        checklist_frame.grid(row=3, column=1, sticky="w", padx=15, pady=(5, 15))

        self.allowed_exts = self.config_manager.get("allowed_extensions", [])
        self.checkbox_vars = {}
        formats = [".epub", ".pdf", ".mobi", ".azw3", ".txt", ".docx"]
        
        for i, fmt in enumerate(formats):
            var = ctk.BooleanVar(value=fmt in self.allowed_exts)
            self.checkbox_vars[fmt] = var
            cb = ctk.CTkCheckBox(checklist_frame, text=fmt.upper(), variable=var)
            cb.grid(row=i // 3, column=i % 3, padx=(0, 15), pady=5)

        # --- Additional App Settings ---
        label_app_title = ctk.CTkLabel(view, text="其他软件设置", font=ctk.CTkFont(size=14, weight="bold"))
        label_app_title.grid(row=2, column=0, sticky="w", padx=10, pady=(15, 5))

        app_frame = ctk.CTkFrame(view)
        app_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.var_min_tray = ctk.BooleanVar(value=self.config_manager.get("minimize_to_tray", True))
        cb_min_tray = ctk.CTkCheckBox(app_frame, text="点击窗口关闭[✕]时最小化到系统托盘，保持后台扫描", variable=self.var_min_tray)
        cb_min_tray.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.var_auto_start = ctk.BooleanVar(value=self.config_manager.get("auto_start_service", False))
        cb_auto_start = ctk.CTkCheckBox(app_frame, text="软件启动时自动开启扫描服务", variable=self.var_auto_start)
        cb_auto_start.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # --- Save Button ---
        btn_save_frame = ctk.CTkFrame(view, fg_color="transparent")
        btn_save_frame.grid(row=4, column=0, padx=10, pady=15, sticky="ew")

        btn_save_settings = ctk.CTkButton(btn_save_frame, text="保存推送设置", width=140, command=self.save_kindle_settings)
        btn_save_settings.pack(side="left", padx=5)

    def browse_folder(self):
        dir_selected = filedialog.askdirectory(title="选择需要监控扫描的目录")
        if dir_selected:
            self.entry_folder.delete(0, "end")
            self.entry_folder.insert(0, os.path.abspath(dir_selected))

    def on_slider_change(self, val):
        self.slider_val = int(val)
        self.slider_label.configure(text=f"{self.slider_val} 分钟")

    def save_kindle_settings(self):
        kindle_email = self.entry_kindle.get().strip()
        folder = self.entry_folder.get().strip()
        
        if not kindle_email or "@" not in kindle_email:
            messagebox.showerror("错误", "请配置正确的 Kindle 接收端邮箱！")
            return

        if folder and not os.path.exists(folder):
            messagebox.showerror("错误", f"配置的扫描目录不存在，请检查路径: {folder}")
            return

        # Build extension filter list
        selected_exts = []
        for ext, var in self.checkbox_vars.items():
            if var.get():
                selected_exts.append(ext)
                if ext == ".mobi":
                    # Add standard synonyms if needed
                    selected_exts.append(".azw")
                if ext == ".docx":
                    selected_exts.append(".doc")

        if not selected_exts:
            messagebox.showerror("错误", "您必须勾选至少一种支持的电子书格式！")
            return

        # Save to settings
        self.config_manager.set("kindle_email", kindle_email)
        self.config_manager.set("scan_folder", folder)
        self.config_manager.set("scan_interval_minutes", self.slider_val)
        self.config_manager.set("allowed_extensions", selected_exts)
        self.config_manager.set("minimize_to_tray", self.var_min_tray.get())
        self.config_manager.set("auto_start_service", self.var_auto_start.get())

        messagebox.showinfo("成功", "推送与目录设置保存成功！")
        
        # If service is currently running, wake it up to apply new settings immediately
        if self.service.is_running:
            self.queue_log("⚙ 推送配置被更新，已自动唤醒后台监控服务应用新配置...", "info")
            self.service.scan_and_send_now()

    # ----------------------------------------------------
    # TAB 4: Sent History View Builder
    # ----------------------------------------------------
    def create_history_view(self):
        view = ctk.CTkFrame(self.container, fg_color="transparent")
        self.views["history"] = view

        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(2, weight=1) # Table expands

        # Header Title
        header = ctk.CTkLabel(view, text="📜 电子书推送历史记录", font=ctk.CTkFont(size=22, weight="bold"))
        header.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 15))

        # Action Buttons bar
        actions_bar = ctk.CTkFrame(view, fg_color="transparent")
        actions_bar.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        btn_refresh = ctk.CTkButton(actions_bar, text="🔄 刷新列表", width=100, height=28, command=self.refresh_history_table)
        btn_refresh.pack(side="left", padx=5)

        btn_clear_hist = ctk.CTkButton(
            actions_bar, text="🗑 清空全部历史", fg_color="#EC7063", hover_color="#C0392B", 
            width=120, height=28, command=self.clear_history
        )
        btn_clear_hist.pack(side="right", padx=5)

        # Table Panel
        self.table_frame = ctk.CTkScrollableFrame(view, label_text="已成功发送的书籍")
        self.table_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.table_frame.grid_columnconfigure((0, 1, 2), weight=1)

    def refresh_history_table(self):
        """Draws the list of sent books as cards in a scrollable frame."""
        # Clear existing children
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        records = self.history_manager.get_all_records()
        self.update_dashboard_stats()

        if not records:
            empty_label = ctk.CTkLabel(self.table_frame, text="🔍 暂无推送记录。在本地目录放入电子书，开启服务即可自动推送！", text_color="gray", pady=40)
            empty_label.grid(row=0, column=0, columnspan=3)
            return

        # Header Row inside scrollable
        header_name = ctk.CTkLabel(self.table_frame, text="书籍名称", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray", anchor="w")
        header_name.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        header_size = ctk.CTkLabel(self.table_frame, text="大小", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray", anchor="center")
        header_size.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        header_time = ctk.CTkLabel(self.table_frame, text="发送时间", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray", anchor="e")
        header_time.grid(row=0, column=2, sticky="ew", padx=10, pady=5)

        # Divider line
        div = ctk.CTkFrame(self.table_frame, height=2, fg_color="gray30")
        div.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 5))

        for idx, rec in enumerate(records):
            row_idx = idx + 2
            
            # Alternating light/dark backgrounds for rows
            bg = "transparent" if idx % 2 == 0 else "gray20"
            row_frame = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=4)
            row_frame.grid(row=row_idx, column=0, columnspan=3, sticky="ew", pady=1)
            row_frame.grid_columnconfigure(0, weight=3) # Book name is wider
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=2)

            name_lbl = ctk.CTkLabel(row_frame, text=rec.get("file_name", ""), font=ctk.CTkFont(size=12), anchor="w")
            name_lbl.grid(row=0, column=0, sticky="w", padx=10, pady=6)

            size_lbl = ctk.CTkLabel(row_frame, text=rec.get("file_size", ""), font=ctk.CTkFont(size=12), anchor="center")
            size_lbl.grid(row=0, column=1, sticky="center", padx=10, pady=6)

            time_lbl = ctk.CTkLabel(row_frame, text=rec.get("sent_at", ""), font=ctk.CTkFont(size=12), anchor="e")
            time_lbl.grid(row=0, column=2, sticky="e", padx=10, pady=6)

    def clear_history(self):
        records = self.history_manager.get_all_records()
        if not records:
            return

        confirm = messagebox.askyesno("确认清空", "这会删除本地数据库的发送记录文件。\n删除后，如果目录里原先的书还在，它们会被再次判定为【未发送】从而被重新发送。\n\n您确认要清空吗？")
        if confirm:
            self.history_manager.clear_history()
            self.refresh_history_table()
            self.queue_log("🗑 推送历史记录已清空。", "warning")

    # ----------------------------------------------------
    # Service Toggle Handlers
    # ----------------------------------------------------
    def toggle_service_via_switch(self):
        """Handler for side switch toggling."""
        active = self.service_switch_var.get()
        if active:
            self.start_service()
        else:
            self.stop_service()

    def start_service(self):
        """Starts the service, updates UI labels, logs status."""
        success = self.service.start()
        if not success:
            self.service_switch_var.set(False)

    def stop_service(self):
        """Stops the service, updates UI labels, logs status."""
        self.service.stop()

    def on_service_status_changed(self, is_running):
        """Callback from KindleService to safely update UI components."""
        # This is safe since we invoke it from service.py or local methods
        if is_running:
            self.service_switch_var.set(True)
            self.service_switch.configure(text="服务开启中")
            self.status_val.configure(text="运行中", text_color="#52BE80")
            
            scan_folder = self.config_manager.get("scan_folder", "未指定")
            self.status_details.configure(text=f"正监控: {os.path.basename(scan_folder)}")
        else:
            self.service_switch_var.set(False)
            self.service_switch.configure(text="服务已关闭")
            self.status_val.configure(text="已停止", text_color="#EC7063")
            self.status_details.configure(text="自动扫描已停止")

    def manual_scan_now(self):
        self.service.scan_and_send_now()

    def open_scan_folder(self):
        folder = self.config_manager.get("scan_folder", "")
        if not folder:
            messagebox.showerror("未指定目录", "您还没有配置本地扫描目录！请前往【目录 & 接收端】配置。")
            return
        
        if not os.path.exists(folder):
            messagebox.showerror("目录不存在", f"本地配置的目录不存在: {folder}")
            return
            
        try:
            os.startfile(folder)
        except Exception as e:
            messagebox.showerror("打开失败", f"无法打开该目录: {e}")

    # ----------------------------------------------------
    # System Tray Integration (pystray)
    # ----------------------------------------------------
    def start_tray_icon(self):
        """Loads assets and spawns a thread for pystray."""
        if not os.path.exists(self.icon_png_path):
            # If assets are not compiled, cannot load tray
            return

        def run_tray():
            import pystray
            
            image = Image.open(self.icon_png_path)
            
            # Tray Menu Items
            menu = (
                pystray.MenuItem("打开 KindleFly", self.tray_show_window, default=True),
                pystray.MenuItem("手动扫描推送", self.tray_scan_now),
                pystray.MenuItem("退出程序", self.tray_exit)
            )
            
            self.tray_icon = pystray.Icon("KindleFly", image, "KindleFly 电子书自动推送", menu)
            self.tray_icon.run()

        self.tray_thread = threading.Thread(target=run_tray, daemon=True)
        self.tray_thread.start()

    def tray_show_window(self, icon=None, item=None):
        self.after(0, self.deiconify)
        self.after(0, self.lift)
        self.after(0, self.focus_force)

    def tray_scan_now(self, icon=None, item=None):
        self.after(0, self.manual_scan_now)

    def tray_exit(self, icon=None, item=None):
        # Stop background service safely
        if self.service.is_running:
            self.service.stop()
            
        if self.tray_icon:
            self.tray_icon.stop()
            
        self.after(0, self.destroy)
        sys.exit(0)

    def on_window_close(self):
        """Intercepts [✕] clicks. Minimizes to tray or exits."""
        if self.var_min_tray.get() and self.tray_icon:
            self.withdraw()
            # Show a brief warning in logs or console
            self.queue_log("ℹ 窗口已关闭，KindleFly 将继续在系统托盘后台运行...", "info")
        else:
            self.tray_exit()

if __name__ == "__main__":
    app = KindleFlyApp()
    app.mainloop()
