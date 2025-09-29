import requests
from time import sleep
import urllib3

# Отключаем предупреждения о небезопасных SSL соединениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Список URL-ов для получения данных о каналах
url_list = [
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=59028300&locationId=1111&from=0&to=9999',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=5471515&locationId=10000081&from=0&to=9999&lang=RUS',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=9119099&locationId=10000081&from=0&to=9999&lang=RUS',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=9119102&locationId=10000081&from=0&to=9999&lang=RUS',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=47320362&locationId=10000081&from=0&to=9999&lang=RUS',
    'http://fe.svc.ott.zala.by/CacheClientJson/json/ChannelPackage/list_channels?channelPackageId=175085983&locationId=10000081&from=0&to=9999&lang=RUS'
]

data = []

# Получаем данные по каждому URL
for url in url_list:
    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            data.append(response.json().get("channels_list", []))
        else:
            print(f"Ошибка при получении данных по ссылке {url}. Код ответа: {response.status_code}")
    except requests.RequestException as e:
        print(f"Ошибка запроса по ссылке {url}: {e}")

# Объединяем и сортируем каналы
channels = [channel for sublist in data for channel in sublist]
channels.sort(key=lambda x: int(x.get("num", 9999)))

playlist = ["#EXTM3U"]
channel_list = []

# Обрабатываем каждый канал
for channel in channels:
    if channel.get("isOttEncrypted") == "0" and channel.get("videoServerProtocol") == "hls":
        bcname = channel.get("bcname", "")
        if bcname in channel_list:
            continue

        # Проверка URL
        ott_url = channel.get("ottURL")
        if isinstance(ott_url, list):
            ott_url = ott_url[0] if ott_url else ""
        elif not isinstance(ott_url, str):
            ott_url = ""

        # Пропускаем, если URL пустой или не содержит схему
        if not ott_url or not ott_url.startswith(("http://", "https://")):
            print(f"Канал {bcname} пропущен: некорректный или пустой ottURL")
            continue

        test_url = ott_url.replace("https://", "http://")

        try:
            response = requests.head(test_url, verify=False, timeout=10)
            if response.status_code == 404:
                print(f"Канал {bcname} недоступен (404)")
                continue
        except requests.RequestException as e:
            print(f"Ошибка при проверке канала {bcname}: {e}")
            continue

        # Добавляем канал в плейлист
        logo = channel.get("logo", "")
        playlist.append(f'#EXTINF:-1 tvg-name="{bcname}" tvg-logo="{logo}",{bcname}')
        playlist.append(ott_url)
        channel_list.append(bcname)
        print(f"Добавлен канал: {channel.get('num')} ({bcname})")

# Сохраняем плейлист в файл
with open("zala.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(playlist))

print("Плейлист IPTV успешно создан!")