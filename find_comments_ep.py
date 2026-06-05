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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "cookie": f"remix_userid={userid}; remix_userkey={userkey}; siteLanguageV2=en",
}

# Try various comment-related endpoints
endpoints = [
    f"/eapi/book/5783016/0e03c3/comments",
    f"/eapi/book/5783016/comments",
    f"/papi/book/5783016/comments",
    f"/papi/book/5783016/0e03c3/comments",
    f"/eapi/user/book/5783016/comments",
]

for ep in endpoints:
    url = f"https://{domain}{ep}"
    try:
        r = req.get(url, headers=headers, proxies=proxies, timeout=8)
        print(f"{ep} => HTTP {r.status_code}")
        try:
            data = r.json()
            print(json.dumps(data, ensure_ascii=False)[:500])
        except:
            print(r.text[:200])
        print()
    except Exception as e:
        print(f"{ep} => ERROR: {e}")
        print()
