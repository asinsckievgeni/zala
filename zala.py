#!/usr/bin/env python3
import requests
import urllib3
import re
from itertools import product

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PACKAGE_IDS = ["59028300", "5471515", "9119099", "9119102", "47320362", "175085983", "46938273"]
LOCATION_IDS = ["1111", "10000081", "10000071", "10000080", "10000082", "10000083", "10000084", "10000085"]
BASE_URL = "http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels"
INFO_DESIRED = "CH_1INFORMVIT_HLS"
LOGO_BASE = "https://asinsckievgeni.github.io/zala/logos"
OUTPUT_FILE = "zala.m3u"
TIMEOUT = 8
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; Mi Box) AppleWebKit/537.36"

def sanitize_for_logo(text):
    cleaned = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\-_.]', '_', str(text))
    return re.sub(r'_+', '_', cleaned).strip('_').lower() or "unknown"

def get_group_title(ch):
    title = ch.get("group_title", "")
    return title.strip() if title and isinstance(title, str) else ""

def main():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Referer": "https://fe.svc.ott.zala.by/"})
    
    all_channels = []
    for pkg, loc in product(PACKAGE_IDS, LOCATION_IDS):
        try:
            resp = session.get(f"{BASE_URL}?channelPackageId={pkg}&locationId={loc}&from=0&to=9999&lang=RUS", verify=False, timeout=TIMEOUT)
            if resp.status_code == 200:
                channels = resp.json().get("channels_list", [])
                if isinstance(channels, list):
                    all_channels.extend(channels)
        except Exception:
            continue
    
    filtered = []
    seen = set()
    info_added = False
    
    for ch in all_channels:
        name = ch.get("bcname", "").strip()
        if not name:
            continue
        
        url = str(ch.get("ottURL") or ch.get("smlOttURL") or ch.get("tstvOttURL") or ch.get("plOttURL") or "").strip()
        if isinstance(ch.get("ottURL"), list):
            url = ch["ottURL"][0] if ch["ottURL"] else ""
        
        if not url.endswith(".m3u8"):
            continue
        
        enc = ch.get("isOttEncrypted")
        if enc is not None and str(enc).strip().lower() not in ("0", "false", ""):
            continue
        
        if ch.get("videoServerProtocol") and ch["videoServerProtocol"] != "hls":
            continue
        
        if name == "Первый информационный":
            if not info_added and INFO_DESIRED in url:
                ch["_final_url"] = url
                filtered.append(ch)
                info_added = True
            continue
        
        if name not in seen:
            ch["_final_url"] = url
            filtered.append(ch)
            seen.add(name)
    
    def safe_int(x):
        try:
            return int(str(x).strip())
        except:
            return 999999
    
    filtered.sort(key=lambda c: safe_int(c.get("num", 999999)))
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in filtered:
            name = str(ch.get("bcname", "Unknown")).strip()
            url = ch.get("_final_url", "")
            if not url.endswith(".m3u8"):
                continue
            logo = f"{LOGO_BASE}/{sanitize_for_logo(name)}.png"
            group = get_group_title(ch)
            f.write(f'#EXTINF:-1 tvg-id="" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n{url}\n')
    
    print(f"\nПлейлист сохранён: {OUTPUT_FILE} ({len(filtered)} каналов)")
    print("\nСписок каналов с номерами:")
    for ch in filtered:
        num = ch.get("num", "")
        name = ch.get("bcname", "Unknown").strip()
        if num:
            print(f"[{num}] {name}")
        else:
            print(f"[---] {name}")

if __name__ == "__main__":
    main()