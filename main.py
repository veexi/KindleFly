import os
import sys
import threading
import webview
from PIL import Image

# KindleFly modules
from config_manager import ConfigManager
from api_bridge import ApiBridge, set_window_ref, log_to_frontend

# Global references
window_ref = None
tray_icon = None
app_bridge = None
config_manager = None

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def tray_show_window(icon=None, item=None):
    """Shows the hidden desktop window."""
    global window_ref
    if window_ref:
        window_ref.show()

def tray_scan_now(icon=None, item=None):
    """Triggers folder scanning from the tray icon."""
    global app_bridge
    if app_bridge:
        app_bridge.manual_scan_now()

def tray_exit(icon=None, item=None):
    """Safely terminates the entire application."""
    global app_bridge, tray_icon, window_ref
    
    print("[KindleFly] Exiting application...")
    
    # 1. Stop backend scanning service
    if app_bridge and app_bridge.service.is_running:
        app_bridge.service.stop()
        
    # 2. Stop tray icon
    if tray_icon:
        try:
            tray_icon.stop()
        except Exception:
            pass
            
    # 3. Destroy webview window (terminates webview.start loop)
    if window_ref:
        try:
            window_ref.destroy()
        except Exception:
            pass
            
    sys.exit(0)

def start_tray_icon():
    """Starts the system tray icon in a separate background thread."""
    global tray_icon
    icon_png_path = resource_path(os.path.join("assets", "app_icon.png"))
    if not os.path.exists(icon_png_path):
        print(f"[KindleFly] Tray icon asset not found: {icon_png_path}")
        return

    def run_tray():
        global tray_icon
        import pystray
        
        try:
            image = Image.open(icon_png_path)
            menu = (
                pystray.MenuItem("打开 KindleFly", tray_show_window, default=True),
                pystray.MenuItem("手动扫描推送", tray_scan_now),
                pystray.MenuItem("退出程序", tray_exit)
            )
            
            tray_icon = pystray.Icon("KindleFly", image, "KindleFly 电子书自动推送", menu)
            tray_icon.run()
        except Exception as e:
            print(f"[KindleFly] Error running tray icon: {e}")

    tray_thread = threading.Thread(target=run_tray, daemon=True)
    tray_thread.start()

def on_closing():
    """Intercepts window close events. Hides window to tray if enabled, else exits cleanly."""
    global config_manager, tray_icon, window_ref, app_bridge
    minimize = config_manager.get("minimize_to_tray", True)

    if minimize and tray_icon:
        # Just hide — return False tells pywebview NOT to destroy the window
        window_ref.hide()
        return False
    else:
        # Spin up a cleanup thread so we don't block the webview event loop
        def _cleanup():
            import time
            try:
                if app_bridge and app_bridge.service.is_running:
                    app_bridge.service.stop()
            except Exception:
                pass
            try:
                if tray_icon:
                    tray_icon.stop()
            except Exception:
                pass
            time.sleep(0.3)
            os._exit(0)  # Hard but clean exit — avoids pywebview hang on Windows

        threading.Thread(target=_cleanup, daemon=True).start()
        return True  # Allow window to begin closing while cleanup runs in background

def main():
    global window_ref, app_bridge, config_manager
    
    # 1. Initialize Configuration
    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_manager = ConfigManager(app_dir)
    
    # 2. Setup backend api bridge
    app_bridge = ApiBridge(app_dir)
    
    # 3. Determine running mode & frontend URL
    # Run with `--dev` argument during development to link directly to Vite dev server
    is_dev = "--dev" in sys.argv
    if is_dev:
        url = "http://localhost:5173"
        print("[KindleFly] Running in DEVELOPMENT mode, connecting to Vite dev server...")
    else:
        # Load local HTML bundle
        html_path = resource_path(os.path.join("frontend", "dist", "index.html"))
        if not os.path.exists(html_path):
            print(f"[KindleFly] Critical Error: Frontend index.html not found at: {html_path}")
            sys.exit(1)
        url = html_path
        print(f"[KindleFly] Running in PRODUCTION mode, loading UI from: {url}")

    # 4. Create native webview window
    window_ref = webview.create_window(
        title="KindleFly v2.0.0",
        url=url,
        js_api=app_bridge,
        width=1020,
        height=680,
        min_size=(960, 600),
        background_color="#121212" # Dark background matches dark theme
    )
    
    # Set references globally for bridge logging
    set_window_ref(window_ref)
    
    # Bind window close event
    window_ref.events.closing += on_closing
    
    # 5. Start system tray icon
    start_tray_icon()
    
    # 6. Auto start background scanner if configured
    if config_manager.get("auto_start_service"):
        # Run slightly delayed to allow webview to load and bind JS callbacks
        def auto_start():
            import time
            time.sleep(1.5)
            app_bridge.toggle_service(True)
        threading.Thread(target=auto_start, daemon=True).start()

    # 7. Start pywebview event loop (blocks main thread)
    webview.start(debug=is_dev)

if __name__ == "__main__":
    main()
