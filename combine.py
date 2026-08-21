import requests
import socket
import concurrent.futures
import random

# Настройки
TIMEOUT = 4
MAX_WORKERS = 200
MAX_CHECK = 500
TARGET_ALIVE = 300
MAX_SERVERS = 500

def extract_host_port(line):
    try:
        hp = line.split("@")[1].split("?")[0]
        host, port = hp.rsplit(":", 1)
        return host, int(port)
    except:
        return None, None

def check_server(line):
    host, port = extract_host_port(line)
    if not host:
        return None
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT):
            return line
    except:
        return None

# Скачиваем подписки
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
                if "security=reality" in raw:
                    if "pbk=" not in raw or "pbk=&" in raw:
                        continue
                all_lines.add(raw)
    except:
        pass

print(f"Всего после фильтрации: {len(all_lines)}")

# Перемешиваем
lines_list = list(all_lines)
random.shuffle(lines_list)

# Проверяем только часть
to_check = lines_list[:MAX_CHECK]
rest = lines_list[MAX_CHECK:]

alive = []
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    results = executor.map(check_server, to_check)
    for res in results:
        if res:
            alive.append(res)
            if len(alive) >= TARGET_ALIVE:
                break

print(f"Живых: {len(alive)}")

# Если живых не хватило, добавляем остальные без проверки
if len(alive) < TARGET_ALIVE:
    needed = TARGET_ALIVE - len(alive)
    alive.extend(rest[:needed])

# Ограничиваем итог
final = alive[:MAX_SERVERS]

with open("merged.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(final))

print(f"Итог: {len(final)}")
