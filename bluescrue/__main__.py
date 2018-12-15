import argparse, bluescrue

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--iface', dest='iface', default=0,
        help='Set Bluetooth device number, 0 (default) for hci0')
    parser.add_argument('-d', '--device', dest='devmac', default=None,
        help='Only listen BLE packets from this BT MAC. For example: -d "fe:ed:ca:fe:ba:be"')
    args = parser.parse_args()

    def callback(decoded):
        print(decoded)

    devices = [args.devmac] if args.devmac else None
    bluescrue.scan(callback, devices, iface=args.iface)
