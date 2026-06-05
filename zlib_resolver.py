import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import threading
import queue

KNOWN_DOMAINS = [
    "z-library.im",   # user-confirmed working domain — tested first
    "z-library.sk",
    "z-library.se",
    "singlelogin.sk",
    "singlelogin.se",
    "singlelogin.rs",
    "singlelogin.as",
    "1lib.sk",
    "1lib.se",
]

def get_request_proxies(proxy_enabled, proxy_type, proxy_host, proxy_port):
    """Build proxies dictionary for requests library."""
    if not proxy_enabled or not proxy_host or not proxy_port:
        return None
    # SOCKS5 proxy URL format: socks5://host:port or socks5h://host:port (performs DNS resolution on proxy)
    protocol = proxy_type.lower()
    if protocol == "socks5":
        # Use socks5h to resolve DNS via proxy to prevent local DNS pollution/blocking
        proxy_url = f"socks5h://{proxy_host}:{proxy_port}"
    else:
        proxy_url = f"http://{proxy_host}:{proxy_port}"
        
    return {
        "http": proxy_url,
        "https": proxy_url
    }

def fetch_wikipedia_domain(proxies=None, timeout=3):
    """Fetches Wikipedia page for Z-Library and extracts the first URL in the infobox."""
    wiki_url = "https://en.wikipedia.org/wiki/Z-Library"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(wiki_url, headers=headers, proxies=proxies, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        infobox = soup.find('table', class_='infobox')
        if not infobox:
            return None

        for row in infobox.find_all('tr'):
            label = row.find('th', class_='infobox-label')
            if label and ('URL' in label.get_text() or 'Website' in label.get_text()):
                data_cell = row.find('td', class_='infobox-data')
                if data_cell:
                    links = data_cell.find_all('a', class_='external')
                    for link in links:
                        href = link.get('href', '')
                        if href.startswith('http'):
                            domain = urlparse(href).netloc
                            if domain:
                                # Strip optional port or www prefix
                                if domain.startswith("www."):
                                    domain = domain[4:]
                                return domain
    except Exception as e:
        print(f"[Zlib Resolver] Error fetching Wikipedia URL: {e}")
    return None

def test_single_domain(domain, proxies=None, timeout=3):
    """Tests if a domain is a working Z-Library EAPI gateway."""
    test_url = f"https://{domain}/eapi/info"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }
    try:
        # Check /eapi/info which is public and returns JSON
        response = requests.get(test_url, headers=headers, proxies=proxies, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, dict) and "success" in data:
                return True
    except Exception:
        pass
    return False

def resolve_working_domain(config_manager, log_callback=None):
    """
    Resolves the best active Z-Library domain.
    1. Returns custom domain if configured and working.
    2. Tries Wikipedia domain.
    3. Tries list of known domains.
    Runs tests in parallel using threads for fast response times.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"[Zlib Resolver] {msg}")

    # Build proxies from configuration
    proxy_enabled = config_manager.get("proxy_enabled", False)
    proxy_type = config_manager.get("proxy_type", "SOCKS5")
    proxy_host = config_manager.get("proxy_host", "127.0.0.1")
    proxy_port = config_manager.get("proxy_port", 7890)
    proxies = get_request_proxies(proxy_enabled, proxy_type, proxy_host, proxy_port)

    # 1. Custom Domain Check
    custom_domain = config_manager.get("zlib_custom_domain", "").strip()
    if custom_domain:
        # Strip https:// or http:// or trailing slashes
        custom_domain = custom_domain.replace("https://", "").replace("http://", "").split("/")[0]
        log(f"测试自定义域名: {custom_domain} ...")
        if test_single_domain(custom_domain, proxies=proxies):
            log(f"自定义域名 {custom_domain} 可用！")
            return custom_domain
        else:
            log(f"⚠ 自定义域名 {custom_domain} 测试失败，将尝试自动解析。")

    # Gather candidate domains to test
    candidates = []
    
    # 2. Try Wikipedia
    log("正在通过维基百科解析 Z-Library 最新域名...")
    wiki_domain = fetch_wikipedia_domain(proxies=proxies)
    if wiki_domain:
        log(f"维基百科解析出域名: {wiki_domain}")
        candidates.append(wiki_domain)
    else:
        log("无法通过维基百科解析，将使用内置备用域名。")

    # Append standard known domains (avoiding duplicates)
    for d in KNOWN_DOMAINS:
        if d not in candidates:
            candidates.append(d)

    log(f"正在并行探活域名列表: {candidates} ...")
    
    # Run tests in parallel to find the fastest responding domain
    result_queue = queue.Queue()
    threads = []
    
    def worker(domain):
        if test_single_domain(domain, proxies=proxies):
            result_queue.put(domain)

    for domain in candidates:
        t = threading.Thread(target=worker, args=(domain,), daemon=True)
        threads.append(t)
        t.start()

    # Wait for the first success or all threads to finish
    # We poll the queue for up to 5 seconds
    import time
    start_time = time.time()
    working_domain = None
    
    while time.time() - start_time < 5.0:
        try:
            working_domain = result_queue.get_nowait()
            break
        except queue.Empty:
            time.sleep(0.1)

    if working_domain:
        log(f"✅ 找到可用的 Z-Library 域名: {working_domain}")
        return working_domain

    log("❌ 未能找到任何可用的 Z-Library 域名，请检查网络或代理设置！")
    return None
