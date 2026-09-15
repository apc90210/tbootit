import urllib.request
import json

ips = [
    '109.109.47.91', '151.234.200.27', '185.199.210.62', '217.151.227.96',
    '5.234.33.68', '37.156.155.65', '2.185.33.41', '192.15.53.101',
    '91.106.76.129', '77.91.92.239'
]

for ip in ips:
    try:
        req = urllib.request.Request(f"http://ip-api.com/json/{ip}", headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
        print(f"{ip}: {data.get('country')} | {data.get('city')} | {data.get('isp')} | {data.get('as')}")
    except Exception as e:
        print(f"{ip}: {e}")
