import os
import json
import base64

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_use_ssl": False,  # False means TLS (port 587), True means SSL (port 465)
    "sender_email": "",
    "smtp_password_obscured": "",  # Obscured using base64
    "kindle_email": "",
    "scan_folder": "",
    "scan_interval_minutes": 10,
    "allowed_extensions": [".epub", ".pdf", ".mobi", ".azw", ".azw3", ".txt", ".docx", ".doc"],
    "minimize_to_tray": True,
    "auto_start_service": False,
    "service_active": False,
    "proxy_enabled": False,
    "proxy_type": "SOCKS5",  # SOCKS5 or HTTP
    "proxy_host": "127.0.0.1",
    "proxy_port": 7890
}

class ConfigManager:
    def __init__(self, config_dir=None):
        if config_dir:
            self.config_path = os.path.join(config_dir, CONFIG_FILE)
        else:
            # If no directory is specified, use the directory where the script is located
            self.config_path = os.path.abspath(CONFIG_FILE)
        self.config = self.load_config()

    def load_config(self):
        """Loads configuration from JSON file. Returns default config if file doesn't exist."""
        if not os.path.exists(self.config_path):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge loaded config with default config to ensure all keys exist
                config = DEFAULT_CONFIG.copy()
                config.update(loaded)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()

    def save_config(self, config_data=None):
        """Saves config_data to JSON file."""
        if config_data is not None:
            self.config = config_data
        
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key, default=None):
        """Gets a configuration value."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Sets a configuration value and saves it."""
        self.config[key] = value
        self.save_config()

    @property
    def smtp_password(self):
        """Decodes the SMTP password from base64."""
        obscured = self.config.get("smtp_password_obscured", "")
        if not obscured:
            return ""
        try:
            return base64.b64decode(obscured.encode("utf-8")).decode("utf-8")
        except Exception:
            return ""

    @smtp_password.setter
    def smtp_password(self, password):
        """Encodes the SMTP password in base64 and saves it."""
        if not password:
            self.config["smtp_password_obscured"] = ""
        else:
            obscured = base64.b64encode(password.encode("utf-8")).decode("utf-8")
            self.config["smtp_password_obscured"] = obscured
        self.save_config()
