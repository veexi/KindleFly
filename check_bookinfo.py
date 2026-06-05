import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from config_manager import ConfigManager
from Zlibrary import Zlibrary
import zlib_resolver

app_dir = os.path.dirname(os.path.abspath(__file__))
cfg = ConfigManager(app_dir)
proxies = zlib_resolver.get_request_proxies(
    cfg.get("proxy_enabled", False), cfg.get("proxy_type","SOCKS5"),
    cfg.get("proxy_host","127.0.0.1"), cfg.get("proxy_port",7890))
client = Zlibrary(
    remix_userid=cfg.get("zlib_remix_userid",""),
    remix_userkey=cfg.get("zlib_remix_userkey",""),
    domain=cfg.get("zlib_last_working_domain","z-library.im"),
    proxies=proxies)

# Check full getBookInfo for 1984
info = client.getBookInfo(5783016, "0e03c3")
print(json.dumps(info, ensure_ascii=False, indent=2))
