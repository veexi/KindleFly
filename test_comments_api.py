"""
Quick test to see what Z-Library EAPI actually returns for comments.
Run: python test_comments_api.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from Zlibrary import Zlibrary
import zlib_resolver
import json

app_dir = os.path.dirname(os.path.abspath(__file__))
cfg = ConfigManager(app_dir)

userid = cfg.get("zlib_remix_userid", "")
userkey = cfg.get("zlib_remix_userkey", "")
domain = cfg.get("zlib_last_working_domain", "z-library.im")

print(f"Domain: {domain}, UserID: {userid}")

client = Zlibrary(remix_userid=userid, remix_userkey=userkey, domain=domain)
print(f"Logged in: {client.isLoggedIn()}")

# 乌合之众 — has 49 comments per screenshot (id=3424735, hash known from search)
# Let's first search for it to get the hash
print("\n--- Searching for 乌合之众 ---")
res = client.search(message="乌合之众 群体心理学", limit=3)
if res and "books" in res:
    for book in res["books"][:3]:
        print(f"ID={book.get('id')}, Hash={book.get('hash')}, Title={book.get('title','')[:40]}")
        
        # Now try comments
        book_id = book.get('id')
        book_hash = book.get('hash')
        if book_id and book_hash:
            print(f"\n--- Comments for {book_id}/{book_hash} ---")
            try:
                comments = client.getBookComments(book_id, book_hash)
                print(f"Response type: {type(comments)}")
                print(f"Full response: {json.dumps(comments, ensure_ascii=False, indent=2)[:2000]}")
            except Exception as e:
                print(f"Error: {e}")
            break
else:
    print(f"Search failed: {res}")
