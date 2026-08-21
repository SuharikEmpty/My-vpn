import requests
import datetime

with open("sources.txt", "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

all_lines = set()

for url in urls:
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            for line in r.text.splitlines():
                line = line.strip()
                if line.startswith(("vless://", "vmess://", "trojan://", "ss://", "hysteria2://")):
                    all_lines.add(line)
    except:
        pass

header = f"# Updated: {datetime.datetime.now()}\n"
with open("merged.txt", "w", encoding="utf-8") as f:
    f.write(header)
    f.write("\n".join(sorted(all_lines)))

print(f"Done. Servers: {len(all_lines)}")
