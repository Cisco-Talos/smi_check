#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Jaime Filson <jafilson@cisco.com>
# Date: 02.26.17

import os
import sys
import uuid
import socket

halt = False

try:
    import argparse
except ImportError:
    print("Missing needed module: argparse")
    halt = True

if halt:
    sys.exit()


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', action='store', dest='ip', required=True, help='IP Address to check')
    parser.add_argument('-r', '--retries', action='store', dest='retries', type=int, default=10, help='Max Retries')
    parser.add_argument('-p', '--port', action='store', dest='port', type=int, default=4786, help='PORT to check')

    global args
    args = parser.parse_args()


def main():
    setup()

    if os.geteuid() != 0:
        print "[ERROR] This script requires root permisions to run"
        print "[ERROR] Please Rerun script with sudo or as root"
        sys.exit()

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.settimeout(10)

    try:
        conn.connect((args.ip, args.port))
    except socket.gaierror:
        print('[ERROR] Could not resolve hostname. Exiting.')
        sys.exit()
    except socket.error:
        print('[ERROR] Could not connect to {0}:{1}. Exiting.'.format(args.ip, args.port))
        print('[WARNING] Either SMI is Disabled, or Firewall is blocking port {0}'.format(args.port))
        sys.exit()

    if conn:
        m_ip = conn.getsockname()[0]

        c_file_name = '{0}'.format(str(uuid.uuid4()).replace('-', ''))

        tftp_conn_string = 'tftp://{0}/{1}'.format(m_ip, c_file_name)

        m_data1 = '0' * 7 + '1' + '0' * 7 + '1' + '0' * 7 + '3' + '0' * 5 + '128' + '0' * 7 + '3' + '0' * 23 + '2' + '0' * 24
        m_data2 = '0' * (264 - len(tftp_conn_string) * 2)

        sTcp = '{0}{1}{2}{3}'.format(m_data1, '0' * 272, tftp_conn_string.encode('hex'), m_data2)

        print('[INFO] Sending TCP probe to {0}:{1}'.format(args.ip, args.port))

        conn.send(sTcp.decode('hex'))
        conn.close()

        print('[INFO] Starting Listener for callbacks')

        tftp_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tftp_conn.settimeout(10)
        tftp_conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            tftp_conn.bind(('', 69))
        except socket.error as e:
            if e.errno == 13:
                print('[ERROR] Invalid Permissions to bind on port 69. Please rerun as root.')
            elif e.errno == 98:
                print('[ERROR] Port 69 is already in use.')
            sys.exit()

        request_count = 0
        error_count = 0

        while True:
            request_count += 1
            print("[INFO] Listening Attempt: {0}".format(request_count))

            if request_count >= args.retries:
                break
            else:

                try:
                    buffer, (ret_ip, ret_port) = tftp_conn.recvfrom(65536)

                    if ret_ip:
                        print('[INFO] Connect back from {0}:{1}'.format(ret_ip, args.port))
                        print('[INFO] Smart Install Client protocol found on {0}:{1}'.format(ret_ip, args.port))
                        break

                except socket.error:
                    error_count += 1
                    if error_count > args.retries:
                        print('[ERROR] Max retry limit reached ({0}). Undetermined.'.format(args.retries))
                        print('[WARNING] Perhaps try again with a larger --retries value'.format(args.retries))
                        break
                except KeyboardInterrupt:
                    print('[ERROR] User ended script early with Control + C')
                    break

        tftp_conn.close()


if __name__ == "__main__":
    main()
