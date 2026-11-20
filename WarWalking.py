import json, subprocess, sys, time
from datetime import datetime

config = {"intervalo": 5.0, "salida": None}
redes = {}  # bssid -> info (búsqueda O(1) y sin duplicados)

def Escanear():
    try:
        r = subprocess.run(
            ["termux-wifi-scaninfo"],
            capture_output=True, text=True, timeout=20
        )
        data = json.loads(r.stdout)
    except FileNotFoundError:sys.exit("Error: falta termux-api. Instala con: pkg install termux-api (y la app Termux:API desde F-Droid).")
    except (subprocess.TimeoutExpired, json.JSONDecodeError):return []
    if isinstance(data, dict):print(f"[!] {data.get('API_ERROR') or data.get('error') or data}");return []
    return data

def Nombre():
    if not config["salida"]:config["salida"] = f"wifiscan_{datetime.now():%Y%m%d_%H%M%S}.json"
    return config["salida"]

def Guardar():
    nombre = Nombre()
    with open(nombre, "w", encoding="utf-8") as f:json.dump(list(redes.values()), f, indent=4, ensure_ascii=False)
    print(f"\n{len(redes)} APs únicos guardados en: {nombre}")

def Procesar(aps):
    ahora = datetime.now().isoformat(timespec="seconds")
    for ap in aps:
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

def Iniciar():
    escaneos = 0
    print(f"Escaneando cada {config['intervalo']}s... (Ctrl+C para volver al menú)")
    try:
        while True:
            Procesar(Escanear())
            escaneos += 1
            if escaneos % 10 == 0:Guardar()
            time.sleep(config["intervalo"])
    except KeyboardInterrupt:print("\nEscaneo detenido!")
    finally:Guardar()

def Intervalo():
    valor = input(f"Segundos entre escaneos [{config['intervalo']}]: ").strip()
    if not valor:return
    try:
        nuevo = float(valor)
        if nuevo <= 0:raise ValueError
        config["intervalo"] = nuevo
        print(f"Intervalo: {nuevo}s")
    except ValueError:print("[!] Valor inválido.")

def Salida():
    valor = input(f"Archivo JSON de salida [{config['salida'] or 'automático'}]: ").strip()
    if valor:config["salida"] = valor if valor.endswith(".json") else valor + ".json";print(f"Archivo: {config['salida']}")

def Ver():
    if not redes:print("Aún no hay redes registradas.");return
    lista = sorted(redes.values(), key=lambda a: a.get("rssi_max") or -999, reverse=True)
    for ap in lista:print(f"{ap['bssid']} | {ap.get('ssid') or '<oculto>':<25} | max {ap['rssi_max']} dBm")
    print(f"\nTotal: {len(redes)} APs")

while True:
    print("\n" + "=" * 46)
    print(" Escáner WiFi Termux")
    print("=" * 46)
    print(f"Intervalo: {config['intervalo']}s | Archivo: {config['salida'] or 'automático'} | APs: {len(redes)}")
    print("-" * 46)
    print("1. Iniciar escaneo")
    print("2. Cambiar intervalo")
    print("3. Cambiar archivo de salida")
    print("4. Ver redes encontradas")
    print("5. Guardar ahora")
    print("0. Salir")
    print("=" * 46)
    
    try:
        match opcion = input("Selecciona una opción: "):
            case "1":Iniciar()
            case "2":Intervalo()
            case "3":Salida()
            case "4":Ver()
            case "5":Guardar()
            case "0":if redes:Guardar()
                print("Hasta luego!")
                break
            case _:print("[!] Opción no válida.")
    except (EOFError, KeyboardInterrupt):print("\nHasta luego.");break
