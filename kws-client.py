#!/usr/bin/env python3
"""
kws-client.py – Client
- Lädt den lokalen Auth-Key und liest die Kontakte aus der Datei contaktd.cdf.
- Sendet in regelmäßigen Abständen (REQUEST_INTERVAL) an jeden Kontakt REQ-Anfragen (z. B. INFO).
- Unterstützt erweiterte REQ-Befehle (z. B. LIST).
- Wenn der Versand fehlschlägt, werden die Nachrichten in data.ksys zwischengespeichert.
- Ein Hintergrund-Thread versucht periodisch, die zwischengespeicherten Nachrichten zu senden.
"""

import os
import socket
import time
from datetime import datetime
import threading

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_KEY_FILE = os.path.join(SCRIPT_DIR, "auth.key")
CONTACT_FILE = os.path.join(SCRIPT_DIR, "contaktd.cdf")
DATATRANS_FILE = os.path.join(SCRIPT_DIR, "datatrans.ksys")
DATA_FILE = os.path.join(SCRIPT_DIR, "data.ksys")

SERVER_PORT = 5000
REQUEST_INTERVAL = 30

def load_auth_key():
    if os.path.exists(AUTH_KEY_FILE):
        with open(AUTH_KEY_FILE, "r") as f:
            return f.read().strip()
    else:
        print("Auth-Key nicht gefunden. Bitte starte zuerst kws.py.")
        exit(1)

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

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATATRANS_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def queue_unsent_message(target_ip, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATA_FILE, "a") as f:
        f.write(f"{target_ip}|{message}|{timestamp}\n")
    log_message(f"Nachricht an {target_ip} in Warteschlange gestellt.")

def send_request_to_target(target_ip, request_msg):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((target_ip, SERVER_PORT))
        s.sendall(request_msg.encode("utf-8"))
        reply = s.recv(4096).decode("utf-8")
        log_message(f"Antwort von {target_ip}: {reply}")
        s.close()
        return True
    except Exception as e:
        log_message(f"Fehler bei Anfrage an {target_ip}: {e}")
        return False

def request_info(auth_key):
    contacts = load_contacts()
    for contact in contacts:
        target_ip = contact["ip_address"]
        request_msg = f"REQ;{auth_key};{contact['auth_id']};INFO"
        if not send_request_to_target(target_ip, request_msg):
            queue_unsent_message(target_ip, request_msg)

def resend_queued_messages(auth_key):
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r") as f:
            lines = f.readlines()
    except Exception:
        return
    unsent = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 2:
            target_ip = parts[0]
            request_msg = parts[1]
            if not send_request_to_target(target_ip, request_msg):
                unsent.append(line)
    with open(DATA_FILE, "w") as f:
        for item in unsent:
            f.write(item + "\n")

def resend_loop(auth_key):
    while True:
        resend_queued_messages(auth_key)
        time.sleep(REQUEST_INTERVAL)

def main():
    auth_key = load_auth_key()
    print("kws-client.py läuft – sende periodisch Anfragen an alle Kontakte.")
    threading.Thread(target=resend_loop, args=(auth_key,), daemon=True).start()
    while True:
        request_info(auth_key)
        time.sleep(REQUEST_INTERVAL)

if __name__ == "__main__":
    main()
