#!/usr/bin/env python3
"""Simple script to interact with a kws_cpp instance.
Usage: python host_bridge.py <ip> <auth-key> <command> [message]
Commands:
  ping       Send a PING and print the response.
  info       Send REQ INFO.
  list       Request the contact list.
  msg <text> Send a text message.
"""
import socket
import sys

SERVER_PORT = 5000

def send_and_recv(ip, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        s.connect((ip, SERVER_PORT))
        s.sendall(message.encode('utf-8'))
        return s.recv(4096).decode('utf-8')

def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    ip = sys.argv[1]
    auth_key = sys.argv[2]
    cmd = sys.argv[3].lower()
    if cmd == 'ping':
        resp = send_and_recv(ip, f"PING;{auth_key}")
        print('Response:', resp)
    elif cmd == 'info':
        resp = send_and_recv(ip, f"REQ;{auth_key};{auth_key};INFO")
        print('Response:', resp)
    elif cmd == 'list':
        resp = send_and_recv(ip, f"REQ;{auth_key};{auth_key};LIST")
        print('Response:', resp)
    elif cmd == 'msg' and len(sys.argv) >= 5:
        text = ' '.join(sys.argv[4:])
        resp = send_and_recv(ip, f"MSG;{auth_key};0;{text}")
        print('Response:', resp)
    else:
        print(__doc__)

if __name__ == '__main__':
    main()
