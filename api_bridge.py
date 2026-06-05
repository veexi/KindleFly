import os
import base64
import threading
import traceback
import json
from datetime import datetime

# KindleFly modules
from config_manager import ConfigManager
from history_manager import HistoryManager
from service import KindleService
from email_sender import EmailSender
from Zlibrary import Zlibrary
import zlib_resolver

window_ref = None
_zlib_client_cache = None
_zlib_client_cache_key = None   # (userid, userkey, domain) — reuse client when unchanged
_zlib_resolved_domain = None

def set_window_ref(window):
    """Sets the pywebview window reference globally for evaluate_js logging."""
    global window_ref
    window_ref = window

def log_to_frontend(message, level="info"):
    """Pushes a log message to the frontend console log panel in real time."""
    global window_ref
    if window_ref:
        # Time formatting
        time_str = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{time_str}] {message}"
        escaped_msg = json.dumps(full_msg)
        try:
            window_ref.evaluate_js(f"if(window.addLog) window.addLog({escaped_msg}, '{level}');")
        except Exception as e:
            print(f"Error evaluating JS log: {e}")

class ApiBridge:
    def __init__(self, app_dir):
        self.app_dir = app_dir
        self.config_manager = ConfigManager(app_dir)
        self.history_manager = HistoryManager(app_dir)
        
        # Initialize background scanning service
        self.service = KindleService(
            config_manager=self.config_manager,
            history_manager=self.history_manager,
            log_callback=log_to_frontend,
            status_callback=self._on_service_status_changed
        )

    def _on_service_status_changed(self, is_running):
        """Notifies frontend when the folder scanner service state changes."""
        global window_ref
        if window_ref:
            try:
                window_ref.evaluate_js(f"if(window.onServiceStatusChanged) window.onServiceStatusChanged({json.dumps(is_running)});")
            except Exception as e:
                print(f"Error notifying service status: {e}")

    # ----------------------------------------------------
    # Configuration Management APIs
    # ----------------------------------------------------
    def get_config(self):
        """Returns the full configuration dictionary (with SMTP and Zlib passwords decrypted)."""
        config = self.config_manager.config.copy()
        # Decode passwords so they can be shown in inputs
        config["smtp_password"] = self.config_manager.smtp_password
        config["zlib_password"] = self.config_manager.zlib_password
        return config

    def save_config(self, new_config):
        """Saves configuration from frontend and updates files."""
        try:
            for key, value in new_config.items():
                if key in ["smtp_password", "zlib_password"]:
                    # These are handled by properties setters
                    continue
                self.config_manager.set(key, value)
            
            # Save obscured passwords
            if "smtp_password" in new_config:
                self.config_manager.smtp_password = new_config["smtp_password"]
            if "zlib_password" in new_config:
                self.config_manager.zlib_password = new_config["zlib_password"]
            
            # If service is running, wake it up to apply new scanning paths or formats
            if self.service.is_running:
                log_to_frontend("配置被更新，正在重新唤醒后台监控...", "info")
                self.service.scan_and_send_now()
                
            return {"success": True, "message": "配置保存成功！"}
        except Exception as e:
            return {"success": False, "message": f"保存配置失败: {str(e)}"}

    # ----------------------------------------------------
    # SMTP Test API
    # ----------------------------------------------------
    def test_smtp_connection(self, config):
        """Runs the SMTP connection test and returns the result."""
        try:
            sender = EmailSender(
                smtp_server=config.get("smtp_server", ""),
                smtp_port=config.get("smtp_port", 587),
                sender_email=config.get("sender_email", ""),
                smtp_password=config.get("smtp_password", ""),
                use_ssl=config.get("smtp_use_ssl", False),
                proxy_enabled=config.get("proxy_enabled", False),
                proxy_type=config.get("proxy_type", "SOCKS5"),
                proxy_host=config.get("proxy_host", "127.0.0.1"),
                proxy_port=config.get("proxy_port", 7890)
            )
            success, msg = sender.test_connection()
            return {"success": success, "message": msg}
        except Exception as e:
            return {"success": False, "message": f"配置校验异常: {str(e)}"}

    # ----------------------------------------------------
    # Service Management APIs
    # ----------------------------------------------------
    def get_service_status(self):
        """Returns whether the scanning service is running."""
        return self.service.is_running

    def toggle_service(self, start):
        """Starts or stops the automatic folder scanner."""
        if start:
            success = self.service.start()
            return {"success": success, "message": "服务已启动" if success else "启动失败，请检查目录及邮件设置！"}
        else:
            success = self.service.stop()
            return {"success": success, "message": "服务已停止"}

    def manual_scan_now(self):
        """Manually triggers directory scanning."""
        self.service.scan_and_send_now()
        return {"success": True, "message": "已触发即时扫描"}

    def open_scan_folder(self):
        """Opens target monitored folder in Windows Explorer."""
        folder = self.config_manager.get("scan_folder", "")
        if not folder or not os.path.exists(folder):
            return {"success": False, "message": "扫描目录不存在或尚未配置！"}
        try:
            os.startfile(folder)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": f"打开失败: {str(e)}"}

    def open_url_in_browser(self, url):
        """Opens a URL in the system default browser (e.g. to view Z-Library comments)."""
        import webbrowser
        try:
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def browse_folder(self):
        """Opens a native Windows folder browser dialog and returns the selected path."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True) # Bring folder picker to front
            folder = filedialog.askdirectory(title="选择需要监控的文件夹")
            root.destroy()
            if folder:
                return os.path.abspath(folder)
        except Exception as e:
            print(f"Error selecting folder: {e}")
        return ""

    # ----------------------------------------------------
    # Push History APIs
    # ----------------------------------------------------
    def get_history(self):
        """Returns all previously sent book records."""
        return self.history_manager.get_all_records()

    def clear_history(self):
        """Clears sent history database."""
        try:
            self.history_manager.clear_history()
            log_to_frontend("已清空推送历史记录。", "warning")
            return {"success": True, "message": "历史记录已清空！"}
        except Exception as e:
            return {"success": False, "message": f"清空失败: {str(e)}"}

    # ----------------------------------------------------
    # Z-Library Integration APIs
    # ----------------------------------------------------
    def get_zlib_domain(self, force_refresh=False):
        """Resolves Z-Library active domain and returns it.
        Caches the last working domain in config to speed up subsequent startups.
        """
        global _zlib_resolved_domain
        if _zlib_resolved_domain and not force_refresh:
            return _zlib_resolved_domain

        # Fast path: test the previously cached domain first
        if not force_refresh:
            cached = self.config_manager.get("zlib_last_working_domain", "")
            if cached:
                log_to_frontend(f"正在验证缓存域名 {cached} ...", "info")
                if zlib_resolver.test_single_domain(cached):
                    _zlib_resolved_domain = cached
                    log_to_frontend(f"✅ 缓存域名 {cached} 仍然可用", "info")
                    return cached
                else:
                    log_to_frontend(f"缓存域名 {cached} 不可用，重新解析中...", "warning")

        # Slow path: full Wikipedia + known domain scan
        domain = zlib_resolver.resolve_working_domain(self.config_manager, log_callback=log_to_frontend)
        if domain:
            _zlib_resolved_domain = domain
            # Persist for next startup
            self.config_manager.set("zlib_last_working_domain", domain)
            return domain
        return ""

    def _get_zlib_client(self):
        """Returns a cached Z-Library client, recreating it only when credentials or domain change."""
        global _zlib_client_cache, _zlib_client_cache_key
        domain = self.get_zlib_domain()
        if not domain:
            raise Exception("未能检测到有效的 Z-Library 域名，请配置自定义域名或网络代理！")

        proxy_enabled = self.config_manager.get("proxy_enabled", False)
        proxy_type = self.config_manager.get("proxy_type", "SOCKS5")
        proxy_host = self.config_manager.get("proxy_host", "127.0.0.1")
        proxy_port = self.config_manager.get("proxy_port", 7890)
        proxies = zlib_resolver.get_request_proxies(proxy_enabled, proxy_type, proxy_host, proxy_port)

        userid = self.config_manager.get("zlib_remix_userid", "")
        userkey = self.config_manager.get("zlib_remix_userkey", "")

        # Build a cache key that captures all identity-affecting parameters
        cache_key = (userid, userkey, domain, proxy_enabled, proxy_host, proxy_port)

        if _zlib_client_cache is not None and _zlib_client_cache_key == cache_key:
            # Reuse existing authenticated client — no extra network request
            return _zlib_client_cache

        # Credentials or domain changed: build a fresh client
        if userid and userkey:
            _zlib_client_cache = Zlibrary(remix_userid=userid, remix_userkey=userkey, domain=domain, proxies=proxies)
        else:
            email = self.config_manager.get("zlib_email", "")
            pwd = self.config_manager.zlib_password
            _zlib_client_cache = Zlibrary(email=email, password=pwd, domain=domain, proxies=proxies)

        _zlib_client_cache_key = cache_key
        return _zlib_client_cache

    def zlib_check_status(self):
        """Checks Z-Library login state and returns user profile if logged in."""
        try:
            client = self._get_zlib_client()
            if client.isLoggedIn():
                profile = client.getProfile()
                if profile.get("success", False):
                    # Cache tokens to config for auto login in the future
                    user_data = profile.get("user", {})
                    self.config_manager.set("zlib_remix_userid", str(user_data.get("id", "")))
                    self.config_manager.set("zlib_remix_userkey", user_data.get("remix_userkey", ""))
                    return {"logged_in": True, "user": user_data, "domain": self.get_zlib_domain()}
            return {"logged_in": False, "domain": self.get_zlib_domain()}
        except Exception as e:
            return {"logged_in": False, "error": str(e), "domain": self.get_zlib_domain()}

    def zlib_login(self, email, password):
        """Logs into Z-Library using email and password."""
        try:
            domain = self.get_zlib_domain()
            if not domain:
                return {"success": False, "message": "未能找到可用的 Z-Library 域名，请检查网络！"}
            
            proxy_enabled = self.config_manager.get("proxy_enabled", False)
            proxy_type = self.config_manager.get("proxy_type", "SOCKS5")
            proxy_host = self.config_manager.get("proxy_host", "127.0.0.1")
            proxy_port = self.config_manager.get("proxy_port", 7890)
            proxies = zlib_resolver.get_request_proxies(proxy_enabled, proxy_type, proxy_host, proxy_port)

            client = Zlibrary(email=email, password=password, domain=domain, proxies=proxies)
            if client.isLoggedIn():
                profile = client.getProfile()
                if profile.get("success", False):
                    user_data = profile.get("user", {})
                    # Save details
                    self.config_manager.set("zlib_email", email)
                    self.config_manager.zlib_password = password
                    self.config_manager.set("zlib_remix_userid", str(user_data.get("id", "")))
                    self.config_manager.set("zlib_remix_userkey", user_data.get("remix_userkey", ""))
                    return {"success": True, "user": user_data}
            
            return {"success": False, "message": "登录失败，请检查账号密码！"}
        except Exception as e:
            return {"success": False, "message": f"登录异常: {str(e)}"}

    def zlib_login_token(self, userid, userkey):
        """Logs into Z-Library using remix cookies token."""
        try:
            domain = self.get_zlib_domain()
            if not domain:
                return {"success": False, "message": "未能找到可用的 Z-Library 域名，请检查网络！"}
                
            proxy_enabled = self.config_manager.get("proxy_enabled", False)
            proxy_type = self.config_manager.get("proxy_type", "SOCKS5")
            proxy_host = self.config_manager.get("proxy_host", "127.0.0.1")
            proxy_port = self.config_manager.get("proxy_port", 7890)
            proxies = zlib_resolver.get_request_proxies(proxy_enabled, proxy_type, proxy_host, proxy_port)

            client = Zlibrary(remix_userid=userid, remix_userkey=userkey, domain=domain, proxies=proxies)
            if client.isLoggedIn():
                profile = client.getProfile()
                if profile.get("success", False):
                    user_data = profile.get("user", {})
                    # Save details
                    self.config_manager.set("zlib_remix_userid", str(userid))
                    self.config_manager.set("zlib_remix_userkey", userkey)
                    self.config_manager.set("zlib_email", user_data.get("email", ""))
                    return {"success": True, "user": user_data}
            
            return {"success": False, "message": "Token 验证失败！"}
        except Exception as e:
            return {"success": False, "message": f"Token 验证异常: {str(e)}"}

    def zlib_logout(self):
        """Logs out from Z-Library by clearing tokens and the client cache."""
        global _zlib_client_cache, _zlib_client_cache_key
        self.config_manager.set("zlib_remix_userid", "")
        self.config_manager.set("zlib_remix_userkey", "")
        self.config_manager.set("zlib_password_obscured", "")
        _zlib_client_cache = None
        _zlib_client_cache_key = None
        return {"success": True}

    def zlib_get_profile(self):
        """Returns full user profile + download quota info."""
        try:
            client = self._get_zlib_client()
            res = client.getProfile()
            if res and res.get("success"):
                return {"success": True, "user": res["user"]}
            return {"success": False, "message": "获取用户信息失败"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def zlib_get_saved_books(self, page=1, limit=20):
        """Returns the user's saved/bookmarked books from Z-Library."""
        try:
            client = self._get_zlib_client()
            res = client.getUserSaved(page=page, limit=limit)
            if res and (res.get("success") or "books" in res):
                books = res.get("books", [])
                return {"success": True, "books": books, "total": len(books)}
            return {"success": False, "message": "获取收藏书单失败", "books": []}
        except Exception as e:
            return {"success": False, "message": str(e), "books": []}

    def zlib_unsave_book(self, book_id):
        """Removes a book from the user's saved list."""
        try:
            client = self._get_zlib_client()
            res = client.unsaveUserBook(book_id)
            if res and res.get("success"):
                return {"success": True}
            return {"success": False, "message": "取消收藏失败"}
        except Exception as e:
            return {"success": False, "message": str(e)}



    def zlib_search(self, query, extension="all", language="all", page=1):
        """Performs search query on Z-Library."""
        try:
            client = self._get_zlib_client()
            ext_list = None
            if extension and extension != "all":
                ext_list = [extension]
                
            lang_param = None
            if language and language != "all":
                lang_param = language

            log_to_frontend(f"正在 Z-Library 搜索: '{query}' (格式: {extension}, 语言: {language}, 页码: {page})...", "info")
            
            # search method returns dict
            result = client.search(
                message=query,
                extensions=ext_list,
                languages=lang_param,
                page=page,
                limit=15
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "message": f"搜索异常: {str(e)}"}

    def zlib_get_recommendations(self):
        """Fetches Z-Library user recommendations."""
        try:
            client = self._get_zlib_client()
            if client.isLoggedIn():
                result = client.getUserRecommended()
                return {"success": True, "data": result}
            return {"success": False, "message": "未登录 Z-Library 账号"}
        except Exception as e:
            return {"success": False, "message": f"获取推荐图书异常: {str(e)}"}

    def zlib_get_popular(self, language=None, page=1):
        """Fetches Z-Library most popular books for a language, defaulting to Chinese."""
        try:
            client = self._get_zlib_client()
            lang = 'chinese' if not language or language == 'all' else language
            result = client.search(languages=lang, order='popular', page=page, limit=20)
            if result and (result.get("success", False) or "books" in result):
                return {"success": True, "data": result}
            else:
                return {"success": False, "message": "获取热门图书失败"}
        except Exception as e:
            return {"success": False, "message": f"获取热门图书异常: {str(e)}"}

    def zlib_get_recently(self, language=None, page=1):
        """Fetches Z-Library recently added books for a language, defaulting to Chinese."""
        try:
            client = self._get_zlib_client()
            lang = 'chinese' if not language or language == 'all' else language
            result = client.search(languages=lang, order='updated', page=page, limit=20)
            if not result or not result.get("books"):
                result = client.search(languages=lang, order='popular', page=page, limit=20)
            if result and (result.get("success", False) or "books" in result):
                return {"success": True, "data": result}
            else:
                return {"success": False, "message": "获取最新图书失败"}
        except Exception as e:
            return {"success": False, "message": f"获取最新图书异常: {str(e)}"}

    def get_book_cover_base64(self, cover_url):
        """Downloads a book cover via Python and returns a base64 data URI.
        Uses a direct requests.get (fast, no auth needed for cover images).
        This is necessary because pywebview loads from file://, which blocks
        cross-origin HTTPS image loads due to browser CORS policy.
        """
        import requests as _requests
        if not cover_url:
            return ""
        try:
            if cover_url.startswith("/"):
                domain = self.get_zlib_domain()
                if not domain:
                    return ""
                cover_url = f"https://{domain}{cover_url}"

            # Build proxy settings if enabled
            proxy_enabled = self.config_manager.get("proxy_enabled", False)
            proxy_type = self.config_manager.get("proxy_type", "SOCKS5")
            proxy_host = self.config_manager.get("proxy_host", "127.0.0.1")
            proxy_port = self.config_manager.get("proxy_port", 7890)
            proxies = zlib_resolver.get_request_proxies(proxy_enabled, proxy_type, proxy_host, proxy_port)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": f"https://{cover_url.split('/')[2]}/",
            }
            resp = _requests.get(cover_url, headers=headers, proxies=proxies, timeout=6, stream=False)
            if resp.status_code == 200 and resp.content:
                mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
                b64 = base64.b64encode(resp.content).decode("utf-8")
                return f"data:{mime};base64,{b64}"
        except Exception as e:
            print(f"[Cover] Failed to load {cover_url}: {e}")
        return ""

    def zlib_push(self, book):
        """Downloads a book to the monitored directory and immediately emails it to Kindle."""
        book_title = book.get("title", "未命名书")
        book_id = book.get("id")
        book_hash = book.get("hash")
        
        if not book_id or not book_hash:
            return {"success": False, "message": "书籍 ID 或 Hash 缺失，无法下载！"}
            
        scan_folder = self.config_manager.get("scan_folder", "")
        kindle_email = self.config_manager.get("kindle_email", "")

        if not scan_folder or not os.path.exists(scan_folder):
            return {"success": False, "message": "请先配置并创建本地监控扫描文件夹！"}
            
        if not kindle_email:
            return {"success": False, "message": "请先配置 Kindle 接收端邮箱！"}

        log_to_frontend(f"📚 开始下载并推送: '{book_title}' ...", "info")
        
        try:
            client = self._get_zlib_client()
            
            # 1. Download file bytes
            log_to_frontend(f"⬇ 正在从 Z-Library 下载电子书...", "info")
            download_result = client.downloadBook(book)
            if not download_result:
                return {"success": False, "message": "文件下载失败，Z-Library 未返回内容。"}
                
            filename, file_bytes = download_result
            # Ensure filename is safe for filesystem
            # Replace invalid chars: \ / : * ? " < > |
            for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                filename = filename.replace(char, '_')
                
            file_path = os.path.join(scan_folder, filename)
            
            # 2. Save locally to monitored folder
            with open(file_path, "wb") as f:
                f.write(file_bytes)
            
            log_to_frontend(f"💾 文件已成功保存至本地: '{filename}'", "success")
            
            # 3. Compute MD5
            file_hash_md5 = self.history_manager.compute_md5(file_path)
            
            # 4. Check email settings and send via SMTP
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
            
            log_to_frontend(f"📧 正在发送邮件推送至 Kindle: {kindle_email}...", "info")
            
            # Send file (run synchronously since this function runs in a background thread of pywebview)
            success, msg = sender.send_book(kindle_email, file_path)
            
            if success:
                log_to_frontend(f"✅ {msg}", "success")
                # Record in sent history
                self.history_manager.mark_as_sent(file_path, file_hash_md5, status="sent")
                return {"success": True, "message": f"成功推送 '{filename}' 至 Kindle！"}
            else:
                log_to_frontend(f"❌ {msg}", "error")
                return {"success": False, "message": f"发送失败: {msg}"}
                
        except Exception as e:
            traceback.print_exc()
            log_to_frontend(f"⚠ 推送异常: {str(e)}", "error")
            return {"success": False, "message": f"推送发生异常: {str(e)}"}

    def zlib_get_book_info(self, book_id, hash_id):
        """Fetches full details of a book from Z-Library."""
        try:
            client = self._get_zlib_client()
            result = client.getBookInfo(book_id, hash_id)
            if result and result.get("success", False):
                return {"success": True, "book": result.get("book", {})}
            else:
                msg = result.get("message", "获取书籍详情失败") if result else "接口未返回数据"
                return {"success": False, "message": msg}
        except Exception as e:
            return {"success": False, "message": f"获取详情异常: {str(e)}"}

    def zlib_save_book(self, book_id):
        """Saves a book to Z-Library user profile (bookmark/favorites)."""
        try:
            client = self._get_zlib_client()
            result = client.saveBook(book_id)
            if result and result.get("success", False):
                return {"success": True, "message": "成功收藏至 Z-Library 个人书库！"}
            else:
                msg = result.get("message", "收藏失败") if result else "接口未返回数据"
                return {"success": False, "message": msg}
        except Exception as e:
            return {"success": False, "message": f"收藏操作异常: {str(e)}"}

    def zlib_unsave_book(self, book_id):
        """Removes a saved book from Z-Library user profile."""
        try:
            client = self._get_zlib_client()
            result = client.unsaveUserBook(book_id)
            if result and result.get("success", False):
                return {"success": True, "message": "成功取消收藏！"}
            else:
                msg = result.get("message", "取消收藏失败") if result else "接口未返回数据"
                return {"success": False, "message": msg}
        except Exception as e:
            return {"success": False, "message": f"取消收藏操作异常: {str(e)}"}

    def zlib_download_only(self, book):
        """Downloads a book to the monitored directory but does not send it via email."""
        book_title = book.get("title", "未命名书")
        book_id = book.get("id")
        book_hash = book.get("hash")
        
        if not book_id or not book_hash:
            return {"success": False, "message": "书籍 ID 或 Hash 缺失，无法下载！"}
            
        scan_folder = self.config_manager.get("scan_folder", "")
        if not scan_folder or not os.path.exists(scan_folder):
            return {"success": False, "message": "请先配置并创建本地监控扫描文件夹！"}

        log_to_frontend(f"📚 开始仅下载: '{book_title}' ...", "info")
        
        try:
            client = self._get_zlib_client()
            
            # 1. Download file bytes
            log_to_frontend(f"⬇ 正在从 Z-Library 下载电子书...", "info")
            download_result = client.downloadBook(book)
            if not download_result:
                return {"success": False, "message": "文件下载失败，Z-Library 未返回内容。"}
                
            filename, file_bytes = download_result
            # Ensure filename is safe for filesystem
            for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                filename = filename.replace(char, '_')
                
            file_path = os.path.join(scan_folder, filename)
            
            # 2. Save locally
            with open(file_path, "wb") as f:
                f.write(file_bytes)
            
            log_to_frontend(f"💾 文件已下载并保存至本地: '{filename}'", "success")
            
            # 3. Compute MD5
            file_hash_md5 = self.history_manager.compute_md5(file_path)
            
            # 4. Mark as downloaded in history to prevent background auto-scanning service from pushing it
            self.history_manager.mark_as_sent(file_path, file_hash_md5, status="downloaded")
            
            return {"success": True, "message": f"成功下载 '{filename}' 至本地！已记录以避免自动推送。"}
        except Exception as e:
            traceback.print_exc()
            log_to_frontend(f"⚠ 下载异常: {str(e)}", "error")
            return {"success": False, "message": f"下载发生异常: {str(e)}"}

    def zlib_get_book_formats(self, book_id, hash_id):
        """Fetches other formats of a book from Z-Library."""
        try:
            client = self._get_zlib_client()
            result = client.getBookForamt(book_id, hash_id)
            if result and result.get("success", False):
                return {"success": True, "formats": result.get("books", [])}
            else:
                return {"success": True, "formats": []}
        except Exception as e:
            return {"success": False, "message": f"获取其他格式异常: {str(e)}"}

    def get_book_comments(self, book_id, book_hash=""):
        """Returns local user notes for a book.
        Note: Z-Library's EAPI does not expose user comments — they are only
        available via the web browser. The frontend should show an 'Open on Z-Library'
        button so users can read real comments in the browser.
        """
        results = []
        comments_file = os.path.join(self.app_dir, "book_comments.json")
        if os.path.exists(comments_file):
            try:
                with open(comments_file, "r", encoding="utf-8") as f:
                    comments_data = json.load(f)
                local_notes = comments_data.get(str(book_id), [])
                for note in local_notes:
                    note["is_local"] = True
                    note["likes"] = 0
                    note.setdefault("avatar_char", (note.get("username") or "我")[0].upper())
                results = local_notes
            except Exception:
                pass
        return results

    def add_book_comment(self, book_id, username, content):
        """Saves a local user note for a book (stored in book_comments.json)."""
        comments_file = os.path.join(self.app_dir, "book_comments.json")
        comments_data = {}
        if os.path.exists(comments_file):
            try:
                with open(comments_file, "r", encoding="utf-8") as f:
                    comments_data = json.load(f)
            except Exception:
                pass

        book_id_str = str(book_id)
        if book_id_str not in comments_data:
            comments_data[book_id_str] = []

        new_note = {
            "username": username or "我",
            "content": content,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "is_local": True,
            "likes": 0,
            "avatar_char": (username or "我")[0].upper(),
        }
        comments_data[book_id_str].insert(0, new_note)

        try:
            with open(comments_file, "w", encoding="utf-8") as f:
                json.dump(comments_data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

        return new_note
