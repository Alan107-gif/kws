#!/usr/bin/env python3
"""
kws.py – Hauptserver
- Legt alle erforderlichen Dateien an (auth.key, config.cfk, contaktd.cdf, datatrans.ksys, data.ksys), falls sie noch nicht existieren.
- Lädt Kontakte aus der Datei contaktd.cdf.
- Startet einen TCP-Server (Port 5000), der eingehende Nachrichten (PING, MSG, REQ) verarbeitet.
- Verarbeitet erweiterte REQ-Befehle: INFO, ADDLIST, LIST.
- Startet einen Hintergrund-Thread, der periodisch alle Kontakte anpingt und deren Status aktualisiert.
- Loggt empfangene Nachrichten in datatrans.ksys (temporär) und in data.ksys (dauerhaft) für nicht abgeschickte Nachrichten.
"""

import os
import socket
import threading
import time
from datetime import datetime
import uuid

# Dateipfade (alle im selben Ordner wie das Script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_KEY_FILE = os.path.join(SCRIPT_DIR, "auth.key")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.cfk")
CONTACT_FILE = os.path.join(SCRIPT_DIR, "contaktd.cdf")
DATATRANS_FILE = os.path.join(SCRIPT_DIR, "datatrans.ksys")
DATA_FILE = os.path.join(SCRIPT_DIR, "data.ksys")  # dauerhafte Speicherung unsent messages

SERVER_PORT = 5000
PING_INTERVAL = 30  # Standard-Pingintervall (in Sekunden)

def create_required_files():
    # auth.key
    if not os.path.exists(AUTH_KEY_FILE):
        key = str(uuid.uuid4())
        with open(AUTH_KEY_FILE, "w") as f:
            f.write(key)
        print(f"Neuer Auth-Key erstellt: {key}")
    else:
        with open(AUTH_KEY_FILE, "r") as f:
            key = f.read().strip()
        print(f"Auth-Key geladen: {key}")
    # config.cfk
    if not os.path.exists(CONFIG_FILE):
        config = {"username": "default_user", "ping_interval": str(PING_INTERVAL)}
        with open(CONFIG_FILE, "w") as f:
            for k, v in config.items():
                f.write(f"{k}={v}\n")
        print("Standard-Konfiguration erstellt.")
    # contaktd.cdf
    if not os.path.exists(CONTACT_FILE):
        open(CONTACT_FILE, "w").close()
        print("Kontaktdatei (contaktd.cdf) erstellt.")
    # datatrans.ksys
    if not os.path.exists(DATATRANS_FILE):
        open(DATATRANS_FILE, "w").close()
        print("Temporäre Logdatei (datatrans.ksys) erstellt.")
    # data.ksys
    if not os.path.exists(DATA_FILE):
        open(DATA_FILE, "w").close()
        print("Permanente Datendatei (data.ksys) erstellt.")
    return key

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    config[k] = v
    return config

def load_contacts():
    contacts = []
    if os.path.exists(CONTACT_FILE):
        with open(CONTACT_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    if line.endswith("|"):
                        line = line[:-1]
                    parts = line.split(";")
                    if len(parts) >= 6:
                        contact = {
                            "username": parts[0],
                            "auth_id": parts[1],
                            "last_contact": parts[2],
                            "user_defined_name": parts[3],
                            "ip_address": parts[4],
                            "status": parts[5]
                        }
                        contacts.append(contact)
    return contacts

def save_contacts(contacts):
    with open(CONTACT_FILE, "w") as f:
        for c in contacts:
            line = f"{c['username']};{c['auth_id']};{c['last_contact']};{c['user_defined_name']};{c['ip_address']};{c['status']}|"
            f.write(line + "\n")

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATATRANS_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def log_permanent(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATA_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def parse_contacts_from_string(data):
    contacts = []
    lines = data.strip().splitlines()
    for line in lines:
        line = line.strip()
        if line:
            if line.endswith("|"):
                line = line[:-1]
            parts = line.split(";")
            if len(parts) >= 6:
                contact = {
                    "username": parts[0],
                    "auth_id": parts[1],
                    "last_contact": parts[2],
                    "user_defined_name": parts[3],
                    "ip_address": parts[4],
                    "status": parts[5]
                }
                contacts.append(contact)
    return contacts

def merge_contacts(existing, new):
    for new_contact in new:
        found = False
        for contact in existing:
            if contact["auth_id"] == new_contact["auth_id"]:
                found = True
                # Bei neueren Kontaktdaten aktualisieren (optional)
                if new_contact["last_contact"] > contact["last_contact"]:
                    contact["last_contact"] = new_contact["last_contact"]
                break
        if not found:
            existing.append(new_contact)
    return existing

def handle_client_connection(conn, addr, auth_key):
    try:
        data = conn.recv(4096).decode("utf-8")
        if not data:
            return
        parts = data.split(";")
        if parts[0] == "PING":
            sender_auth = parts[1] if len(parts) > 1 else "unknown"
            print(f"PING von {addr} (Auth: {sender_auth})")
            conn.sendall("PONG".encode("utf-8"))
            log_message(f"PING von {addr} (Auth: {sender_auth})")
        elif parts[0] == "MSG":
            if len(parts) >= 4:
                sender_auth = parts[1]
                msg_time = parts[2]
                message_content = ";".join(parts[3:])
                print(f"MSG von {addr} (Auth: {sender_auth}): {message_content}")
                log_message(f"MSG von {sender_auth}: {message_content} (um {msg_time})")
                conn.sendall("MSG_RECEIVED".encode("utf-8"))
        elif parts[0] == "REQ":
            if len(parts) >= 4:
                sender_auth = parts[1]
                target_auth = parts[2]
                command = parts[3].upper()
                payload = ""
                if len(parts) > 4:
                    payload = ";".join(parts[4:])
                if target_auth != auth_key:
                    conn.sendall("WRONG_TARGET".encode("utf-8"))
                    log_message(f"REQ von {addr} für falsches Ziel: {target_auth} (meine Auth: {auth_key})")
                else:
                    if command == "INFO":
                        response = f"INFO;{auth_key}"
                        conn.sendall(response.encode("utf-8"))
                        log_message(f"INFO-Anfrage von {addr} beantwortet.")
                    elif command == "ADDLIST":
                        # Erwartet: payload enthält die übertragene Kontaktliste
                        if payload:
                            new_contacts = parse_contacts_from_string(payload)
                            existing_contacts = load_contacts()
                            merged = merge_contacts(existing_contacts, new_contacts)
                            save_contacts(merged)
                            conn.sendall("ADDLIST_RECEIVED".encode("utf-8"))
                            log_message(f"ADDLIST von {addr} verarbeitet, Kontakte aktualisiert.")
                        else:
                            conn.sendall("NO_PAYLOAD".encode("utf-8"))
                    elif command == "LIST":
                        with open(CONTACT_FILE, "r") as f:
                            contacts_data = f.read().strip()
                        response = f"LIST;{contacts_data}"
                        conn.sendall(response.encode("utf-8"))
                        log_message(f"LIST-Anfrage von {addr} beantwortet.")
                    else:
                        conn.sendall("UNBEKANNT_COMMAND".encode("utf-8"))
            else:
                conn.sendall("INVALID_REQ_FORMAT".encode("utf-8"))
        else:
            conn.sendall("UNKNOWN_COMMAND".encode("utf-8"))
    except Exception as e:
        print("Fehler bei der Verbindung:", e)
    finally:
        conn.close()

def server_loop(auth_key):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", SERVER_PORT))
    server_socket.listen(5)
    print(f"kws.py: Server läuft auf Port {SERVER_PORT}.")
    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client_connection, args=(conn, addr, auth_key), daemon=True).start()

def ping_contacts(auth_key):
    while True:
        contacts = load_contacts()
        updated = False
        for contact in contacts:
            ip = contact["ip_address"]
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((ip, SERVER_PORT))
                s.sendall(f"PING;{auth_key}".encode("utf-8"))
                reply = s.recv(1024).decode("utf-8")
                if reply == "PONG":
                    contact["status"] = "online"
                    contact["last_contact"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{contact['user_defined_name']} ({ip}) ist online.")
                s.close()
            except Exception as e:
                contact["status"] = "offline"
                print(f"{contact['user_defined_name']} ({ip}) ist offline.")
            updated = True
        if updated:
            save_contacts(contacts)
        time.sleep(PING_INTERVAL)

def main():
    auth_key = create_required_files()
    config = load_config()
    global PING_INTERVAL
    if "ping_interval" in config:
        try:
            PING_INTERVAL = int(config["ping_interval"])
        except:
            pass
    threading.Thread(target=server_loop, args=(auth_key,), daemon=True).start()
    threading.Thread(target=ping_contacts, args=(auth_key,), daemon=True).start()
    print("kws.py läuft. Drücke STRG+C zum Beenden.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server wird beendet.")

if __name__ == "__main__":
    main()
