"""
Test getUserSaved, getUserDownloaded, getMostPopular, getProfile responses.
Run: python test_profile_api.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_manager import ConfigManager
from Zlibrary import Zlibrary

app_dir = os.path.dirname(os.path.abspath(__file__))
cfg = ConfigManager(app_dir)
userid = cfg.get("zlib_remix_userid", "")
userkey = cfg.get("zlib_remix_userkey", "")
domain = cfg.get("zlib_last_working_domain", "z-library.im")

client = Zlibrary(remix_userid=userid, remix_userkey=userkey, domain=domain)
print(f"Logged in: {client.isLoggedIn()}\n")

def dump(label, data):
    print(f"=== {label} ===")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    print()

dump("getProfile", client.getProfile())
dump("getUserSaved (limit=5)", client.getUserSaved(limit=5))
dump("getUserDownloaded (limit=5)", client.getUserDownloaded(limit=5))
