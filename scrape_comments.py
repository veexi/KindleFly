import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from config_manager import ConfigManager
import zlib_resolver, requests as req

app_dir = os.path.dirname(os.path.abspath(__file__))
cfg = ConfigManager(app_dir)
userid  = cfg.get("zlib_remix_userid", "")
userkey = cfg.get("zlib_remix_userkey", "")
domain  = cfg.get("zlib_last_working_domain", "z-library.im")
proxies = zlib_resolver.get_request_proxies(
    cfg.get("proxy_enabled", False), cfg.get("proxy_type", "SOCKS5"),
    cfg.get("proxy_host", "127.0.0.1"), cfg.get("proxy_port", 7890))

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": f"remix_userid={userid}; remix_userkey={userkey}; siteLanguageV2=en",
}

# 1984 book href from earlier test
href = "/book/K5dMKErOko/1984.html"
url = f"https://{domain}{href}"
print(f"Fetching: {url}")

r = req.get(url, headers=headers, proxies=proxies, timeout=15)
print(f"HTTP {r.status_code}, content-length={len(r.content)}")

html = r.text

# Look for comment-related patterns
patterns = [
    r'class="[^"]*comment[^"]*"',
    r'"comments?":\s*\[',
    r'id="comments?"',
    r'data-comment',
    r'commentCount',
    r'z-comments',
]

print("\n--- Pattern matches ---")
for p in patterns:
    matches = re.findall(p, html, re.IGNORECASE)
    if matches:
        print(f"  {p!r} => {matches[:3]}")

# Extract a chunk around "comment"
idx = html.lower().find("comment")
if idx >= 0:
    print(f"\n--- Context around 'comment' (pos {idx}) ---")
    print(html[max(0,idx-100):idx+500])

# Also check for JSON data embedded in script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(scripts):
    if 'comment' in s.lower():
        print(f"\n--- Script {i} contains 'comment' ---")
        print(s[:1000])
