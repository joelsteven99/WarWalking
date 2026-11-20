import socket, struct
from datetime import datetime

PROTOCOLOS = {1: "ICMP", 6: "TCP", 17: "UDP"}
FILTROS = {"1": ("Todos", None), "2": ("TCP", 6), "3": ("UDP", 17), "4": ("ICMP", 1)}

config = {"maximo": 0, "payload": 64, "filtro": "1"}

def MacStr(raw):return ":".join(f"{b:02x}" for b in raw)

def ParseEthernet(data):dest, src, proto = struct.unpack("!6s6sH", data[:14]);return MacStr(dest), MacStr(src), proto, data[14:]

def ParseIpv4(data):
    ihl = (data[0] & 0x0F) * 4
    ttl, proto, src, dst = struct.unpack("!8xBB2x4s4s", data[:20])
    return ttl, proto, socket.inet_ntoa(src), socket.inet_ntoa(dst), data[ihl:]

def ParseTcp(data):
    sport, dport, seq, ack, offset_flags = struct.unpack("!HHLLH", data[:14])
    offset = (offset_flags >> 12) * 4
    flags = offset_flags & 0x3F
    nombres = ["FIN", "SYN", "RST", "PSH", "ACK", "URG"]
    activos = [n for i, n in enumerate(nombres) if flags & (1 << i)]
    return sport, dport, seq, ack, activos, data[offset:]

def ParseUdp(data):sport, dport, size = struct.unpack("!HHH2x", data[:8]);return sport, dport, size, data[8:]

def ParseIcmp(data):tipo, codigo, checksum = struct.unpack("!BBH", data[:4]);return tipo, codigo, checksum, data[4:]

def MostrarPayload(payload):
    if not payload or config["payload"] == 0:return
    parte = payload[:config["payload"]]
    texto = "".join(chr(b) if 32 <= b < 127 else "." for b in parte)
    print(f"    Payload ({len(payload)} bytes): {texto}")

def Capturar():
    try:sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
    except PermissionError:print("[!] Se necesitan permisos root. Ejecuta 'tsu' primero.");return
    except AttributeError:print("[!] AF_PACKET no está disponible en este sistema.");return

    filtro = FILTROS[config["filtro"]][1]
    print("[*] Capturando paquetes... (Ctrl+C para volver al menú)\n")
    contador = 0
    try:
        while True:
            data, _ = sock.recvfrom(65535)
            dst_mac, src_mac, eth_proto, payload = ParseEthernet(data)

            if eth_proto == 0x0800:ttl, proto, src, dst, payload = ParseIpv4(payload)
            if filtro and (eth_proto != 0x0800 or proto != filtro):continue

            contador += 1
            hora = datetime.now().strftime("%H:%M:%S")
            print(f"[{contador}] {hora} | Eth {src_mac} -> {dst_mac} | tipo 0x{eth_proto:04x}")

            if eth_proto == 0x0800:
                nombre = PROTOCOLOS.get(proto, str(proto))
                print(f"    IPv4 {src} -> {dst} | {nombre} | TTL {ttl}")
                if proto == 6 and len(payload) >= 14:
                    sp, dp, seq, ack, flags, datos = ParseTcp(payload)
                    print(f"    TCP {sp} -> {dp} | flags: {','.join(flags) or '-'}")
                    MostrarPayload(datos)
                elif proto == 17 and len(payload) >= 8:
                    sp, dp, size, datos = ParseUdp(payload)
                    print(f"    UDP {sp} -> {dp} | largo {size}")
                    MostrarPayload(datos)
                elif proto == 1 and len(payload) >= 4:
                    tipo, codigo, _, datos = ParseIcmp(payload)
                    print(f"    ICMP tipo {tipo} código {codigo}")
            elif eth_proto == 0x0806:print("    ARP")
            elif eth_proto == 0x86DD:print("    IPv6")
            print()
            if config["maximo"] and contador >= config["maximo"]:break
    except KeyboardInterrupt:pass
    finally:sock.close();print(f"\n[*] Captura finalizada. Paquetes capturados: {contador}")

def Maximo():
    valor = input(f"Máximo de paquetes, 0 = sin límite [{config['maximo']}]: ").strip()
    if not valor:return
    try:
        nuevo = int(valor)
        if nuevo < 0:raise ValueError
        config["maximo"] = nuevo
        print(f"[*] Máximo: {nuevo or 'sin límite'}")
    except ValueError:print("[!] Valor inválido.")

def Payload():
    valor = input(f"Bytes de payload a mostrar, 0 = ocultar [{config['payload']}]: ").strip()
    if not valor:return
    try:
        nuevo = int(valor)
        if nuevo < 0:raise ValueError
        config["payload"] = nuevo
        print(f"[*] Payload: {nuevo} bytes")
    except ValueError:print("[!] Valor inválido.")

def Filtro():
    for clave, (nombre, _) in FILTROS.items():print(f"  {clave}. {nombre}")
    valor = input(f"Filtro [{FILTROS[config['filtro']][0]}]: ").strip()
    if not valor:return
    match valor:
        case "1" | "2" | "3" | "4":config["filtro"] = valor;print(f"[*] Filtro: {FILTROS[valor][0]}")
        case _:print("[!] Opción no válida.")

while True:
    print("\n" + "=" * 46)
    print(" Capturador de paquetes ")
    print("=" * 46)
    print(f"Máximo: {config['maximo'] or 'sin límite'} | Payload: {config['payload']} bytes"
          f" | Filtro: {FILTROS[config['filtro']][0]}")
    print("-" * 46)
    print("1. Iniciar captura")
    print("2. Configurar máximo de paquetes")
    print("3. Configurar bytes de payload")
    print("4. Filtrar por protocolo")
    print("0. Salir")
    print("=" * 46)

    try:
        match input("Opción: ").strip():
            case "1":Capturar()
            case "2":Maximo()
            case "3":Payload()
            case "4":Filtro()
            case "0":print("Hasta luego!");break
            case _:print("[!] Opción no válida.")
    except (KeyboardInterrupt, EOFError):print("\nScript detenido!")
