import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import json

# Add project root to path
sys.path.append(r"c:\Users\mjddw\Desktop\个人博客\KindleFly")

from Zlibrary import Zlibrary
from config_manager import ConfigManager
import zlib_resolver

config_manager = ConfigManager(r"c:\Users\mjddw\Desktop\个人博客\KindleFly")
domain = zlib_resolver.resolve_working_domain(config_manager)
proxy_enabled = config_manager.get("proxy_enabled", False)
proxy_type = config_manager.get("proxy_type", "SOCKS5")
proxy_host = config_manager.get("proxy_host", "127.0.0.1")
proxy_port = config_manager.get("proxy_port", 7890)
proxies = zlib_resolver.get_request_proxies(proxy_enabled, proxy_type, proxy_host, proxy_port)

userid = config_manager.get("zlib_remix_userid", "")
userkey = config_manager.get("zlib_remix_userkey", "")

client = Zlibrary(remix_userid=userid, remix_userkey=userkey, domain=domain, proxies=proxies)
if client.isLoggedIn():
    print("Logged in successfully!")
    recs = client.getUserRecommended()
    if recs and recs.get("success", False) and recs.get("books"):
        book = recs["books"][0]
        print(f"Fetching formats for book: {book['title']} (ID: {book['id']}, Hash: {book['hash']})")
        formats = client.getBookForamt(book["id"], book["hash"])
        print("\nFormats Response:")
        print(json.dumps(formats, indent=2, ensure_ascii=False))
    else:
        print("Failed to fetch recommendations or no books found.")
else:
    print("Login failed.")
