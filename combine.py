import requests
import json
import subprocess
import socket
import random
import time
import os

# Настройки
CHECK_URL = "http://www.gstatic.com/generate_204"
TIMEOUT = 8
MAX_CHECK = 300

def get_free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def test_server(line):
    port = get_free_port()

    # Конфиг для Xray
    conf = {
        "inbounds": [{
            "listen": "127.0.0.1",
            "port": port,
            "protocol": "socks",
            "settings": {"udp": True}
        }],
        "outbounds": []
    }

    try:
        if line.startswith("vless://"):
            rest = line.replace("vless://", "", 1)
            if "#" in rest:
                rest = rest.split("#")[0]
            uuid, hp = rest.split("@", 1)
            host_port, params = hp.split("?", 1) if "?" in hp else (hp, "")
            host, port_s = host_port.rsplit(":", 1)
            port_s = int(port_s)

            outbound = {
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": host,
                        "port": port_s,
                        "users": [{"id": uuid, "encryption": "none"}]
                    }]
                }
            }

            if "security=reality" in params:
                # REALITY требует доп. настроек, пропускаем для простоты
                return None

            conf["outbounds"].append(outbound)

        elif line.startswith("trojan://"):
            rest = line.replace("trojan://", "", 1)
            if "#" in rest:
                rest = rest.split("#")[0]
            uuid, hp = rest.split("@", 1)
            host_port, params = hp.split("?", 1) if "?" in hp else (hp, "")
            host, port_s = host_port.rsplit(":", 1)
            port_s = int(port_s)

            outbound = {
                "protocol": "trojan",
                "settings": {
                    "servers": [{
                        "address": host,
                        "port": port_s,
                        "password": uuid
                    }]
                }
            }
            conf["outbounds"].append(outbound)

        elif line.startswith("vmess://"):
            import base64
            b64 = line.replace("vmess://", "", 1)
            raw = base64.b64decode(b64 + "==").decode("utf-8")
            outbound = json.loads(raw)
            conf["outbounds"].append(outbound)

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
        r = requests.get(
            CHECK_URL,
            proxies={"http": f"socks5://127.0.0.1:{port}", "https": f"socks5://127.0.0.1:{port}"},
            timeout=TIMEOUT
        )
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
                if not raw.startswith(("vless://", "vmess://", "trojan://")):
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
        print(f"ALIVE: {line[:60]}")

print(f"Живых: {len(alive)}")

# Сохраняем
with open("merged.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(alive))

print(f"Итог: {len(alive)}")
