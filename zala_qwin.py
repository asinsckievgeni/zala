import requests
from time import sleep
import urllib3

# Отключаем предупреждения о небезопасных SSL соединениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url_list = [
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=59028300&locationId=1111&from=0&to=9999',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=5471515&locationId=10000081&from=0&to=9999&lang=RUS',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=9119099&locationId=10000081&from=0&to=9999&lang=RUS',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=9119102&locationId=10000081&from=0&to=9999&lang=RUS',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=47320362&locationId=10000081&from=0&to=9999&lang=RUS',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=175085983&locationId=10000081&from=0&to=9999&lang=RUS'
]

data = []

# Проходим по каждому URL в списке url_list
for url in url_list:
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        data.append(response.json()["channels_list"])
    else:
        print(f"Ошибка при получении данных по ссылке {url}. Код ответа: {response.status_code}")

# Объединяем все полученные данные в один список
data = [channel for sublist in data for channel in sublist]
# Сортируем каналы по num
data.sort(key=lambda x: int(x["num"]))

playlist = []
channel_list = []

playlist.append("#EXTM3U")

for channel in data:
    # Проверяем, что канал не зашифрован и использует HLS
    if channel["isOttEncrypted"] == "0" and channel["videoServerProtocol"] == "hls":
        # Пропускаем дубликаты
        if channel["bcname"] in channel_list:
            continue

        # Получаем URL для проверки
        ott_url_raw = channel["ottURL"]
        if isinstance(ott_url_raw, list):
            if len(ott_url_raw) == 0:
                print(f"Канал {channel['bcname']} — пустой список URL, пропускаем")
                continue
            test_url = ott_url_raw[0].replace("https://", "http://")
        elif isinstance(ott_url_raw, str):
            test_url = ott_url_raw.replace("https://", "http://")
        else:
            print(f"Канал {channel['bcname']} — неизвестный тип ottURL: {type(ott_url_raw)}, пропускаем")
            continue

        # Проверяем доступность URL
        try:
            response = requests.head(test_url, verify=False, timeout=10)
            if response.status_code == 404:
                print(f"Канал {channel['bcname']} недоступен (404), пропускаем")
                continue
            # Можно также проверить другие коды, например != 200, но 404 — основной индикатор
        except requests.RequestException as e:
            print(f"Ошибка при проверке канала {channel['bcname']}: {e}, пропускаем")
            continue

        # Добавляем канал в плейлист
        playlist.append(f'#EXTINF:-1 tvg-name="{channel["bcname"]}" tvg-logo="{channel["logo"]}",{channel["bcname"]}')
        
        # Вставляем в плейлист тот же URL, что и проверяли (или первый из списка)
        if isinstance(channel["ottURL"], list):
            stream_url = channel["ottURL"][0]  # берем первый URL
        else:
            stream_url = channel["ottURL"]

        playlist.append(stream_url)
        channel_list.append(channel["bcname"])
        print(f"Добавлен канал: {channel['num']} ({channel['bcname']})")

# Сохраняем плейлист в файл
with open("zala.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(playlist))

print("Плейлист IPTV успешно создан!")