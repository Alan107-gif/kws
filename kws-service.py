#!/usr/bin/env python3
"""
kws-service.py – Benutzeroberfläche
Verfügbare Befehle:
  Help
      Zeigt diese Hilfe an.
  Add <auth-id>
      Fügt einen neuen Kontakt hinzu. Anschließend werden weitere Details (Benutzername, Anzeigename, IP) abgefragt.
  List
      Listet alle in contaktd.cdf gespeicherten Kontakte auf.
  Message <user_defined_name> <Nachricht>
      Sendet eine Nachricht an den angegebenen Kontakt.
  Show
      Zeigt den Inhalt der temporären Logdatei (datatrans.ksys) an.
  Request <auth-id/user_defined_name> <Befehl>
      Sendet eine Anfrage an den Kontakt. Unterstützte Befehle: INFO, ADDLIST, LIST.
      Bei ADDLIST wird die eigene Kontaktliste als Payload gesendet.
"""

import os
import socket
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_KEY_FILE = os.path.join(SCRIPT_DIR, "auth.key")
CONTACT_FILE = os.path.join(SCRIPT_DIR, "contaktd.cdf")
DATATRANS_FILE = os.path.join(SCRIPT_DIR, "datatrans.ksys")
DATA_FILE = os.path.join(SCRIPT_DIR, "data.ksys")
SERVER_PORT = 5000

def load_auth_key():
    if os.path.exists(AUTH_KEY_FILE):
        with open(AUTH_KEY_FILE, "r") as f:
            return f.read().strip()
    else:
        print("Auth-Key nicht gefunden. Bitte installiere zuerst kws.")
        sys.exit(1)

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

def save_contact(contact):
    contacts = load_contacts()
    contacts.append(contact)
    with open(CONTACT_FILE, "w") as f:
        for c in contacts:
            line = f"{c['username']};{c['auth_id']};{c['last_contact']};{c['user_defined_name']};{c['ip_address']};{c['status']}|"
            f.write(line + "\n")

def list_contacts():
    contacts = load_contacts()
    if not contacts:
        print("Keine Kontakte gefunden.")
        return
    print("Kontakte:")
    for c in contacts:
        print(f"Name: {c['user_defined_name']}, Auth-ID: {c['auth_id']}, IP: {c['ip_address']}, Status: {c['status']}, Letzter Kontakt: {c['last_contact']}")

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATATRANS_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def queue_unsent_message(target_ip, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATA_FILE, "a") as f:
        f.write(f"{target_ip}|{message}|{timestamp}\n")
    log_message(f"Nachricht an {target_ip} in Warteschlange gestellt.")

def send_request(target_ip, target_auth, command, auth_key, payload=""):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((target_ip, SERVER_PORT))
        req = f"REQ;{auth_key};{target_auth};{command.upper()}"
        if payload:
            req += f";{payload}"
        s.sendall(req.encode("utf-8"))
        reply = s.recv(4096).decode("utf-8")
        log_message(f"Antwort von {target_ip}: {reply}")
        s.close()
    except Exception as e:
        log_message(f"Fehler bei der Anfrage an {target_ip}: {e}")
        queue_unsent_message(target_ip, f"REQ;{auth_key};{target_auth};{command.upper()}" + (f";{payload}" if payload else ""))

def send_message(ip, message, auth_key):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, SERVER_PORT))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"MSG;{auth_key};{timestamp};{message}"
        s.sendall(msg.encode("utf-8"))
        reply = s.recv(4096).decode("utf-8")
        if reply == "MSG_RECEIVED":
            log_message(f"Nachricht an {ip} wurde bestätigt.")
        s.close()
    except Exception as e:
        log_message(f"Fehler beim Senden an {ip}: {e}")
        queue_unsent_message(ip, f"MSG;{auth_key};{datetime.now().strftime('%Y-%m-%d %H:%M:%S')};{message}")

def show_messages():
    if os.path.exists(DATATRANS_FILE):
        with open(DATATRANS_FILE, "r") as f:
            print(f.read())
    else:
        print("Keine Nachrichten vorhanden.")

def print_help():
    help_text = """
Verfügbare Befehle:
  Help
      Zeigt diese Hilfe an.
  Add <auth-id>
      Fügt einen neuen Kontakt hinzu. Danach werden weitere Details (Benutzername, Anzeigename, IP) abgefragt.
  List
      Listet alle Kontakte auf.
  Message <user_defined_name> <Nachricht>
      Sendet eine Nachricht an den angegebenen Kontakt.
  Show
      Zeigt alle empfangenen Nachrichten (datatrans.ksys).
  Request <auth-id/user_defined_name> <Befehl>
      Sendet eine Anfrage an den Kontakt.
      Unterstützte Befehle: INFO, ADDLIST, LIST.
      Bei ADDLIST wird die eigene Kontaktliste als Payload gesendet.
"""
    print(help_text)

def main():
    auth_key = load_auth_key()
    print("kws-service gestartet. Tippe 'Help' für Befehle.")
    while True:
        try:
            command = input(">> ").strip()
            if not command:
                continue
            parts = command.split()
            cmd = parts[0].lower()
            if cmd == "help":
                print_help()
            elif cmd == "add":
                if len(parts) < 2:
                    print("Usage: Add <auth-id>")
                    continue
                new_auth = parts[1]
                username = input("Benutzername: ").strip()
                user_defined_name = input("Anzeigename: ").strip()
                ip_address = input("IP-Adresse: ").strip()
                last_contact = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status = "offline"
                contact = {
                    "username": username,
                    "auth_id": new_auth,
                    "last_contact": last_contact,
                    "user_defined_name": user_defined_name,
                    "ip_address": ip_address,
                    "status": status
                }
                save_contact(contact)
                print("Kontakt hinzugefügt.")
            elif cmd == "list":
                list_contacts()
            elif cmd == "message":
                if len(parts) < 3:
                    print("Usage: Message <user_defined_name> <Nachricht>")
                    continue
                target_name = parts[1]
                message_content = " ".join(parts[2:])
                contacts = load_contacts()
                target = None
                for c in contacts:
                    if c["user_defined_name"] == target_name:
                        target = c
                        break
                if target:
                    send_message(target["ip_address"], message_content, auth_key)
                else:
                    print("Kontakt nicht gefunden.")
            elif cmd == "show":
                show_messages()
            elif cmd == "request":
                if len(parts) < 3:
                    print("Usage: Request <auth-id/user_defined_name> <Befehl>")
                    continue
                target_identifier = parts[1]
                req_command = parts[2].lower()
                contacts = load_contacts()
                target = None
                for c in contacts:
                    if c["auth_id"] == target_identifier or c["user_defined_name"] == target_identifier:
                        target = c
                        break
                if target:
                    if req_command == "addlist":
                        # Lese die eigene Kontaktliste als Payload
                        if os.path.exists(CONTACT_FILE):
                            with open(CONTACT_FILE, "r") as f:
                                payload = f.read().strip()
                        else:
                            payload = ""
                        send_request(target["ip_address"], target["auth_id"], "ADDLIST", auth_key, payload)
                    elif req_command == "list":
                        send_request(target["ip_address"], target["auth_id"], "LIST", auth_key)
                    else:
                        send_request(target["ip_address"], target["auth_id"], req_command, auth_key)
                else:
                    print("Kontakt nicht gefunden.")
            else:
                print("Unbekannter Befehl. Tippe 'Help' für Befehle.")
        except KeyboardInterrupt:
            print("Beende kws-service.")
            break
        except Exception as e:
            print("Fehler:", e)

if __name__ == "__main__":
    main()
