import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

package_ids = [
    "59028300", "5471515", "9119099", "9119102",
    "47320362", "175085983", "46938273"
]
location_ids = ["1111", "10000081", "10000071", "10000080", "10000082", "10000083", "10000084", "10000085"]

url_list = []
for pkg in package_ids:
    for loc in location_ids:
        url_list.append(
            f"http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels"
            f"?channelPackageId={pkg}&locationId={loc}&from=0&to=9999&lang=RUS"
        )

all_channels = []

for url in url_list:
    try:
        response = requests.get(url, verify=False, timeout=8)
        if response.status_code != 200:
            continue
        data = response.json()
        channels = data.get("channels_list", [])
        all_channels.extend(channels)
    except Exception:
        continue

# === Правильные идентификаторы в URL ===
INFO_DESIRED = "CH_1INFORMVIT_HLS"
BEL4_DESIRED = "CH_BELARUS4VIT_HLS"  # ← ИСПРАВЛЕНО!

filtered_channels = []
seen_names = set()
info_added = False
bel4_added = False

for ch in all_channels:
    bcname = ch.get("bcname", "")
    if not bcname:
        continue

    ott_url = (
        ch.get("ottURL") or
        ch.get("smlOttURL") or
        ch.get("tstvOttURL") or
        ch.get("plOttURL") or
        ""
    )
    if isinstance(ott_url, list):
        ott_url = ott_url[0] if ott_url else ""
    ott_url = str(ott_url).strip()

    if not ott_url.endswith(".m3u8"):
        continue

    is_encrypted = ch.get("isOttEncrypted")
    if is_encrypted is not None:
        is_encrypted = str(is_encrypted).strip()
        if is_encrypted not in ("0", "false", ""):
            continue

    protocol = ch.get("videoServerProtocol")
    if protocol and protocol != "hls":
        continue

    # === Первый информационный ===
    if bcname == "Первый информационный":
        if not info_added and INFO_DESIRED in ott_url:
            ch["_final_url"] = ott_url
            filtered_channels.append(ch)
            info_added = True
        continue

    # === Беларусь 4 (все варианты имени) ===
    if bcname.startswith("Беларусь 4"):
        if not bel4_added and BEL4_DESIRED in ott_url:
            ch["_final_url"] = ott_url
            filtered_channels.append(ch)
            bel4_added = True
        continue

    # === Остальные каналы ===
    if bcname not in seen_names:
        ch["_final_url"] = ott_url
        filtered_channels.append(ch)
        seen_names.add(bcname)

# Сортировка
def safe_int(x):
    try:
        return int(x)
    except:
        return 999999

filtered_channels.sort(key=lambda c: safe_int(c.get("num", 999999)))

print("Найденные каналы:")
for ch in filtered_channels:
    num = ch.get("num", "").strip()
    bcname = ch.get("bcname", "Unknown").strip()
    print(f"[{num}] {bcname}")

# Запись плейлиста
with open("zala.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for ch in filtered_channels:
        bcname = str(ch.get("bcname", "Unknown")).strip()
        logo = str(ch.get("logo", "")).strip()
        ott_url = ch.get("_final_url", "")

        if not ott_url.endswith(".m3u8"):
            continue

        f.write(f'#EXTINF:-1 tvg-name="{bcname}" tvg-logo="{logo}",{bcname}\n')
        f.write(f'{ott_url}\n')

print(f"\nПлейлист сохранен: zala.m3u ({len(filtered_channels)} каналов)")