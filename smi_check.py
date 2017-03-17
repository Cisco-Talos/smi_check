#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Michael Schueler <mschuele@cisco.com>
# Based on work by: Jaime Filson <jafilson@cisco.com>
# Date: 2017-03-17

import sys
import socket

halt = False

try:
    import argparse
except ImportError:
    print('Missing needed module: argparse')
    halt = True

if halt:
    sys.exit()


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', action='store', dest='ip', required=True, help='IP Address to check')
    parser.add_argument('-p', '--port', action='store', dest='port', type=int, default=4786, help='PORT to check')

    global args
    args = parser.parse_args()


def main():
    setup()

    CONN_TIMEOUT = 10

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.settimeout(CONN_TIMEOUT)

    try:
        conn.connect((args.ip, args.port))
    except socket.gaierror:
        print('[ERROR] Could not resolve hostname. Exiting.')
        sys.exit()
    except socket.error:
        print('[ERROR] Could not connect to {0}:{1}'.format(args.ip, args.port))
        print('[INFO] Either Smart Install feature is Disabled, or Firewall is blocking port {0}'.format(args.port))
        print('[INFO] {0} is not affected'.format(args.ip))
        sys.exit()

    if conn:
        req = '0' * 7 + '1' + '0' * 7 + '1' + '0' * 7 + '4' + '0' * 7 + '8' + '0' * 7 + '1' + '0' * 8
        resp = '0' * 7 + '4' + '0' * 8 + '0' * 7 + '3' + '0' * 7 + '8' + '0' * 7 + '1' + '0' * 8

        print('[INFO] Sending TCP probe to {0}:{1}'.format(args.ip, args.port))

        conn.send(req.decode('hex'))

        while True:
            try:
                data = conn.recv(512)

                if (len(data) < 1):
                    print('[INFO] Smart Install Director feature active on {0}:{1}'.format(args.ip, args.port))
                    print('[INFO] {0} is not affected'.format(args.ip))
                    break
                elif (len(data) == 24):
                    if (data.encode('hex') == resp):
                        print('[INFO] Smart Install Client feature active on {0}:{1}'.format(args.ip, args.port))
                        print('[INFO] {0} is affected'.format(args.ip))
                        break
                    else:
                        print(
                        '[ERROR] Unexpected response received, Smart Install Client feature might be active on {0}:{1}'.format(
                            args.ip, args.port))
                        print('[INFO] Unclear whether {0} is affected or not'.format(args.ip))
                        break
                else:
                    print(
                    '[ERROR] Unexpected response received, Smart Install Client feature might be active on {0}:{1}'.format(
                        args.ip, args.port))
                    print('[INFO] Unclear whether {0} is affected or not'.format(args.ip))
                    break

            except socket.error:
                print('[ERROR] No response after {0} seconds (default connection timeout)'.format(CONN_TIMEOUT))
                print('[INFO] Unclear whether {0} is affected or not'.format(args.ip))
                break

            except KeyboardInterrupt:
                print('[ERROR] User ended script early with Control + C')
                break

        conn.close()


if __name__ == "__main__":
    main()
