import requests
import socket
import ssl
import concurrent.futures
import random

# Настройки
TIMEOUT = 5
MAX_WORKERS = 200

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

    # 1. TCP-проверка
    try:
        sock = socket.create_connection((host, port), timeout=TIMEOUT)
    except:
        return None

    # 2. TLS-проверка
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(sock, server_hostname=host) as tls:
            if tls.getpeercert():
                return line
    except:
        pass

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

# Проверяем все
alive = []
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    results = executor.map(check_server, lines_list)
    for res in results:
        if res:
            alive.append(res)

print(f"Живых: {len(alive)}")

# Сохраняем только живых
with open("merged.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(alive))

print(f"Итог: {len(alive)}")
