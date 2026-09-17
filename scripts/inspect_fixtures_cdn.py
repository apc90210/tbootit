import glob
import re

for f in glob.glob('chrome-extension/technoreboot-avito/tests/fixtures/*'):
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        c = fp.read()
    urls = re.findall(r'https?://[^\s"\'<>\\]*img\.avito\.st[^\s"\'<>\\]*', c)
    if urls:
        print(f"{f}: found {len(urls)} urls")
        for u in urls[:5]:
            print(f"   {u}")
