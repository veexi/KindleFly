"""
Debug Z-Library API endpoints with proxy support.
Run: .venv\Scripts\python debug_api.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from Zlibrary import Zlibrary
import zlib_resolver

app_dir = os.path.dirname(os.path.abspath(__file__))
cfg = ConfigManager(app_dir)

userid  = cfg.get("zlib_remix_userid", "")
userkey = cfg.get("zlib_remix_userkey", "")
domain  = cfg.get("zlib_last_working_domain", "z-library.im")

# Read proxy from config
proxy_enabled = cfg.get("proxy_enabled", False)
proxy_type    = cfg.get("proxy_type", "SOCKS5")
proxy_host    = cfg.get("proxy_host", "127.0.0.1")
proxy_port    = cfg.get("proxy_port", 7890)
proxies = zlib_resolver.get_request_proxies(proxy_enabled, proxy_type, proxy_host, proxy_port)

print(f"Domain  : {domain}")
print(f"UserID  : {userid}")
print(f"Proxies : {proxies}")
print()

client = Zlibrary(remix_userid=userid, remix_userkey=userkey, domain=domain, proxies=proxies)
print(f"Logged in: {client.isLoggedIn()}\n")

def dump(label, data):
    s = json.dumps(data, ensure_ascii=False, indent=2)
    print(f"=== {label} ===")
    print(s[:4000])
    print()

# 1. Profile
dump("getProfile", client.getProfile())

# 2. Saved books
dump("getUserSaved(limit=5)", client.getUserSaved(limit=5))

# 3. Downloaded books
dump("getUserDownloaded(limit=5)", client.getUserDownloaded(limit=5))

# 4. Comments - search first, then get comments
print("=== Searching for '时生' ===")
res = client.search(message="时生 东野圭吾", limit=3)
if res and "books" in res:
    book = res["books"][0]
    bid   = book.get("id")
    bhash = book.get("hash")
    title = book.get("title", "")[:50]
    print(f"Found: {title}  id={bid}  hash={bhash}\n")
    dump(f"getBookComments({bid}, {bhash})", client.getBookComments(bid, bhash))
else:
    print(f"Search result: {res}")
