import os
import time
import threading
from datetime import datetime, timedelta
from email_sender import EmailSender

class KindleService:
    def __init__(self, config_manager, history_manager, log_callback=None, status_callback=None):
        """
        :param config_manager: ConfigManager instance
        :param history_manager: HistoryManager instance
        :param log_callback: Function to call for logging: log_callback(message, level)
                             levels: 'info', 'success', 'warning', 'error', 'debug'
        :param status_callback: Function to call to update run status: status_callback(is_running)
        """
        self.config_manager = config_manager
        self.history_manager = history_manager
        self.log_callback = log_callback
        self.status_callback = status_callback
        
        self._thread = None
        self._stop_event = threading.Event()
        self._sleep_event = threading.Event()
        self.is_running = False
        self.last_scan_time = None
        self.next_scan_time = None

    def log(self, message, level="info"):
        if self.log_callback:
            # Timestamp formatting inside GUI console looks premium
            time_str = datetime.now().strftime("%H:%M:%S")
            self.log_callback(f"[{time_str}] {message}", level)
        else:
            print(f"[{level.upper()}] {message}")

    def start(self):
        """Starts the background scanning service thread."""
        if self.is_running or (self._thread and self._thread.is_alive()):
            self.log("服务已经在运行中。", "warning")
            return False

        self.config_manager.set("service_active", True)
        self._stop_event.clear()
        self._sleep_event.clear()
        self.is_running = True
        
        if self.status_callback:
            self.status_callback(True)

        self._thread = threading.Thread(target=self._service_loop, daemon=True)
        self._thread.start()
        self.log("▶ KindleFly 自动扫描服务已启动...", "success")
        return True

    def stop(self):
        """Stops the background scanning service thread."""
        if not self.is_running:
            self.log("服务并未运行。", "warning")
            return False

        self.log("正在停止扫描服务...", "info")
        self.config_manager.set("service_active", False)
        self._stop_event.set()
        self._sleep_event.set() # Wake up sleeping thread immediately to let it exit
        self.is_running = False
        self.next_scan_time = None
        
        if self.status_callback:
            self.status_callback(False)
            
        self.log("⏹ KindleFly 自动扫描服务已停止。", "info")
        return True

    def scan_and_send_now(self):
        """Runs a single scan and send cycle immediately or wakes up the running thread."""
        if not self.is_running:
            self.log("⚙ 执行单次手动扫描...", "info")
            self._stop_event.clear()
            scan_thread = threading.Thread(target=self._perform_scan, args=(True,), daemon=True)
            scan_thread.start()
        else:
            self.log("⚙ 正在唤醒后台监控线程进行即时扫描...", "info")
            self._sleep_event.set()

    def _service_loop(self):
        """Main service loop running inside background thread."""
        # Initial scan on startup
        self._perform_scan()

        while not self._stop_event.is_set():
            interval_mins = max(1, int(self.config_manager.get("scan_interval_minutes", 10)))
            self.next_scan_time = datetime.now() + timedelta(minutes=interval_mins)
            
            self._sleep_event.clear()
            
            # Safe and responsive sleep utilizing threading.Event.wait()
            self._sleep_event.wait(timeout=interval_mins * 60)

            # If stopped during sleep, don't scan
            if self._stop_event.is_set():
                break

            self._perform_scan()

    def _perform_scan(self, is_manual=False):
        """Scans the target folder and sends any new books found."""
        scan_folder = self.config_manager.get("scan_folder", "")
        kindle_email = self.config_manager.get("kindle_email", "")

        # Valdiate settings
        if not scan_folder:
            self.log("⚠ 未配置扫描目录！请在配置面板中指定文件夹。", "error")
            if is_manual: return
            # Sleep 30s before retrying to avoid spamming the log in auto mode
            time.sleep(30)
            return
            
        if not os.path.exists(scan_folder):
            self.log(f"⚠ 扫描目录不存在: {scan_folder}，请检查配置！", "error")
            if is_manual: return
            time.sleep(30)
            return

        if not kindle_email:
            self.log("⚠ 未配置接收端 Kindle 邮箱！无法推送。", "error")
            if is_manual: return
            time.sleep(30)
            return

        # Initialize email sender
        try:
            sender = EmailSender(
                smtp_server=self.config_manager.get("smtp_server", "smtp.gmail.com"),
                smtp_port=self.config_manager.get("smtp_port", 587),
                sender_email=self.config_manager.get("sender_email", ""),
                smtp_password=self.config_manager.smtp_password,
                use_ssl=self.config_manager.get("smtp_use_ssl", False),
                proxy_enabled=self.config_manager.get("proxy_enabled", False),
                proxy_type=self.config_manager.get("proxy_type", "SOCKS5"),
                proxy_host=self.config_manager.get("proxy_host", "127.0.0.1"),
                proxy_port=self.config_manager.get("proxy_port", 7890)
            )
        except Exception as e:
            self.log(f"⚠ 初始化发信服务失败: {e}", "error")
            return

        self.last_scan_time = datetime.now()
        self.log(f"🔍 启动目录扫描: {scan_folder}", "info")

        allowed_exts = [ext.lower() for ext in self.config_manager.get("allowed_extensions", [])]
        
        try:
            # Get list of files in scan folder
            files = [f for f in os.listdir(scan_folder) if os.path.isfile(os.path.join(scan_folder, f))]
        except Exception as e:
            self.log(f"⚠ 读取扫描目录失败: {e}", "error")
            return

        matching_files = []
        for file in files:
            _, ext = os.path.splitext(file.lower())
            if ext in allowed_exts:
                matching_files.append(os.path.join(scan_folder, file))

        if not matching_files:
            self.log("✔ 未在该文件夹中发现匹配的电子书格式。", "info")
            return

        self.log(f"📄 发现 {len(matching_files)} 个符合条件的电子书文件，正在检查是否已发送过...", "info")
        
        unsent_books = []
        for file_path in matching_files:
            file_hash = self.history_manager.compute_md5(file_path)
            if not file_hash:
                continue
            
            if not self.history_manager.is_already_sent(file_path, file_hash):
                unsent_books.append((file_path, file_hash))

        if not unsent_books:
            self.log("✔ 文件夹中所有的电子书都已经推送过了，无新书需要处理。", "success")
            return

        self.log(f"🚀 发现 {len(unsent_books)} 本新电子书，开始发送...", "info")

        success_count = 0
        fail_count = 0

        for file_path, file_hash in unsent_books:
            file_name = os.path.basename(file_path)
            self.log(f"📧 正在发送: {file_name} ...", "info")
            
            # Send file
            success, msg = sender.send_book(kindle_email, file_path)
            
            if success:
                success_count += 1
                self.log(f"✅ {msg}", "success")
                # Record in sent history database
                self.history_manager.mark_as_sent(file_path, file_hash)
            else:
                fail_count += 1
                self.log(f"❌ {msg}", "error")
                # Wait 10 seconds before next attempt if failed, to avoid rapid-fire errors
                time.sleep(10)
            
            # Short throttle delay (3 seconds) between sends to be polite to Gmail SMTP rate limits
            time.sleep(3)

        self.log(f"✨ 扫描发送完成！本次成功推送: {success_count} 本，失败: {fail_count} 本。", "success" if fail_count == 0 else "warning")
