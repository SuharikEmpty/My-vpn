import requests

with open("sources.txt", "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

all_lines = set()

for url in urls:
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            for raw in r.text.splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                if not raw.startswith(("vless://", "vmess://", "trojan://", "ss://", "hysteria2://")):
                    continue
                raw = raw.split("#")[0]
                all_lines.add(raw)
    except:
        pass

with open("merged.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(all_lines)))

print(f"Done. Servers: {len(all_lines)}")
