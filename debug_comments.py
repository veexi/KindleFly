import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from config_manager import ConfigManager
from Zlibrary import Zlibrary
import zlib_resolver, requests as req

app_dir = os.path.dirname(os.path.abspath(__file__))
cfg = ConfigManager(app_dir)

userid  = cfg.get("zlib_remix_userid", "")
userkey = cfg.get("zlib_remix_userkey", "")
domain  = cfg.get("zlib_last_working_domain", "z-library.im")
proxies = zlib_resolver.get_request_proxies(
    cfg.get("proxy_enabled", False), cfg.get("proxy_type", "SOCKS5"),
    cfg.get("proxy_host", "127.0.0.1"), cfg.get("proxy_port", 7890))

client = Zlibrary(remix_userid=userid, remix_userkey=userkey, domain=domain, proxies=proxies)
print(f"Logged in: {client.isLoggedIn()}")

# Search and get first book
res = client.search(message="1984 george orwell", limit=3)
book = res["books"][0]
bid, bhash = book["id"], book["hash"]
print(f"Book: id={bid} hash={bhash}")

# Try comments endpoint
cres = client.getBookComments(bid, bhash)
print("=== getBookComments response ===")
print(json.dumps(cres, ensure_ascii=False, indent=2))
