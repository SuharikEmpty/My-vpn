import requests
import json
import subprocess
import socket
import random
import time
import os
import signal

# Настройки
CHECK_URL = "http://www.gstatic.com/generate_204"
TIMEOUT = 8
MAX_WORKERS = 20  # меньше, потому что Xray жрёт память
MAX_CHECK = 300   # сколько серверов проверяем

def get_free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def test_server(line):
    port = get_free_port()
    conf = {
        "inbounds": [{
            "listen": "127.0.0.1",
            "port": port,
            "protocol": "socks",
            "settings": {"udp": True}
        }],
        "outbounds": [{
            "protocol": "vless",
            "settings": {"vnext": []}
        }]
    }

    # Парсим строку
    try:
        if line.startswith("vless://"):
            # vless://uuid@host:port?params#name
            rest = line.replace("vless://", "", 1)
            if "#" in rest:
                rest = rest.split("#")[0]
            uuid, hp = rest.split("@", 1)
            host, port_s = hp.split("?", 1)[0].rsplit(":", 1)
            params = hp.split("?", 1)[1] if "?" in hp else ""
            port = int(port_s)
            conf["outbounds"][0]["protocol"] = "vless"
            conf["outbounds"][0]["settings"] = {
                "vnext": [{
                    "address": host,
                    "port": port,
                    "users": [{"id": uuid, "encryption": "none"}]
                }]
            }
            if "security=reality" in params:
                # Упрощённо: REALITY требует доп. параметров, пропускаем
                return None
        elif line.startswith("vmess://"):
            import base64
            b64 = line.replace("vmess://", "", 1)
            raw = base64.b64decode(b64 + "==").decode("utf-8")
            conf["outbounds"][0] = json.loads(raw)
        elif line.startswith("trojan://"):
            rest = line.replace("trojan://", "", 1)
            if "#" in rest:
                rest = rest.split("#")[0]
            uuid, hp = rest.split("@", 1)
            host, port_s = hp.split("?", 1)[0].rsplit(":", 1)
            port = int(port_s)
            conf["outbounds"][0]["protocol"] = "trojan"
            conf["outbounds"][0]["settings"] = {
                "servers": [{"address": host, "port": port, "password": uuid}]
            }
        else:
            return None
    except:
        return None

    # Запускаем Xray
    conf_file = f"/tmp/xray_{port}.json"
    with open(conf_file, "w") as f:
        json.dump(conf, f)

    proc = subprocess.Popen(
        ["./xray", "run", "-c", conf_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(1)

    try:
        r = requests.get(CHECK_URL, proxies={"http": f"socks5://127.0.0.1:{port}", "https": f"socks5://127.0.0.1:{port}"}, timeout=TIMEOUT)
        if r.status_code == 204:
            return line
    except:
        pass
    finally:
        proc.terminate()
        try:
            os.remove(conf_file)
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
                all_lines.add(raw)
    except:
        pass

print(f"Всего после фильтрации: {len(all_lines)}")

# Перемешиваем и ограничиваем
lines_list = list(all_lines)
random.shuffle(lines_list)
to_check = lines_list[:MAX_CHECK]

# Проверяем
alive = []
for line in to_check:
    if test_server(line):
        alive.append(line)
        print(f"ALIVE: {line[:50]}")
    if len(alive) % 10 == 0 and len(alive) > 0:
        print(f"Найдено живых: {len(alive)}")

# Сохраняем
with open("merged.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(alive))

print(f"Итог: {len(alive)}")
