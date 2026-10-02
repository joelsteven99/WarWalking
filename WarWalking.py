#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime

def escanear():
    try:
        r = subprocess.run(
            ["termux-wifi-scaninfo"],
            capture_output=True, text=True, timeout=20
        )
        data = json.loads(r.stdout)
    except FileNotFoundError:
        sys.exit("Error: falta termux-api. Instala con: pkg install termux-api ""(y la app Termux:API desde F-Droid).")
    except (subprocess.TimeoutExpired, json.JSONDecodeError):return []
    if isinstance(data, dict):print(f"[!] {data.get('API_ERROR') or data.get('error') or data}");return []
    return data

def guardar(redes, nombre):
    with open(nombre, "w", encoding="utf-8") as f:
        json.dump(list(redes.values()), f, indent=4, ensure_ascii=False)

parser = argparse.ArgumentParser(description="Escáner de redes WiFi para Termux")
parser.add_argument("-i", "--intervalo", type=float, default=5,help="segundos entre escaneos (por defecto 5)")
parser.add_argument("-o", "--salida", default=None,help="nombre del archivo JSON de salida")
args = parser.parse_args()

nombre = args.salida or f"wifiscan_{datetime.now():%Y%m%d_%H%M%S}.json"
redes = {}  # bssid -> info (búsqueda O(1) y sin duplicados)
escaneos = 0

print(f"Escaneando cada {args.intervalo}s... (Ctrl+C para detener)")
try:
    while True:
        ahora = datetime.now().isoformat(timespec="seconds")
        for ap in escanear():
            bssid = ap.get("bssid")
            if not bssid:continue
            rssi = ap.get("rssi")

            if bssid not in redes:
                ap["primera_vez"] = ahora
                ap["ultima_vez"] = ahora
                ap["rssi_max"] = rssi
                redes[bssid] = ap
                print(f"Nuevo AP: {bssid} | {ap.get('ssid') or '<oculto>'} | {rssi} dBm")
            else:
                reg = redes[bssid]
                reg["ultima_vez"] = ahora
                if rssi is not None and (reg["rssi_max"] is None or rssi > reg["rssi_max"]):reg["rssi_max"] = rssi

        escaneos += 1
        if escaneos % 10 == 0:guardar(redes, nombre)
        time.sleep(args.intervalo)
except KeyboardInterrupt:print("\nScript detenido!")
finally:guardar(redes, nombre);print(f"\n{len(redes)} APs únicos guardados en: {nombre}")
