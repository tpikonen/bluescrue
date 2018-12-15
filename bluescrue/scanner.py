import threading, subprocess, psutil, time, logging
from bluepy.btle import Scanner, DefaultDelegate, BTLEException, BluepyHelper
from bluescrue.decode import *


log = logging.getLogger(__name__)

## bluepy scanner

class ScanDelegate(DefaultDelegate):
    def __init__(self, ev, callback, devices=None, raw=False):
        DefaultDelegate.__init__(self)
        self.ev = ev
        self.cb = callback
        self.raw = raw
        self.devices = devices
    def handleDiscovery(self, dev, isNewDev, isNewData):
        self.ev.set()
        if self.devices and not dev.addr in self.devices: return
        for (adtype, desc, value) in dev.getScanData():
            if adtype==255 and value[:4]=="9904": # Ruuvitag
                if self.raw:
                    self.cb((value, dev.addr, dev.rssi))
                else:
                    intime = time.time()
                    data = bytearray.fromhex(value[4:])
                    decoded = ruuvitag_decode(data)
                    decoded["mac"] = dev.addr
                    decoded["rssi"] = dev.rssi
                    decoded["time"] = intime
                    self.cb(decoded)

# Set up a reset thread with Threading

def reset_btadapter():
    """Issue commands to make a Bluetooth adapter work again.

    Capabilities 'cap_net_raw,cap_net_admin+eip' need to be given to
    hciconfig and hcitool (man 8 setcap).
    """
    # FIXME: Use psutil for killing.
    def kill_child_processes(parent_pid):
        try:
            parent = psutil.Process(parent_pid)
        except psutil.NoSuchProcess:
            return
        for process in parent.children(recursive=True):
            subprocess.call(['kill', '-s', 'SIGINT', str(process.pid)])

    # do a 'sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hciconfig`' to avoid sudo
    #subprocess.call('hciconfig hci0 reset', shell=True, stdout=subprocess.DEVNULL)
    subprocess.call('hciconfig hci0 reset', shell=True)
    #hcitool = subprocess.Popen(['hcitool', 'lescan', '--duplicates'], stdout=subprocess.DEVNULL)
    hcitool = subprocess.Popen(['hcitool', 'lescan', '--duplicates'])
    time.sleep(10)
    kill_child_processes(hcitool.pid)
    subprocess.call(['kill', '-s', 'SIGINT', str(hcitool.pid)])


def idlereset(ev, timeout=10.0, reset_deadtime=300.0):
    """Reset the bluetooth adapter if event is not set in timeout seconds."""
    lastreset = 0.0
    while True:
        ev.clear()
        if (not ev.wait(timeout)) and (time.time() - lastreset > reset_deadtime):
            log.info("Reset!")
            reset_btadapter()
            log.info("Done resetting.")
            lastreset = time.time()


def scan(callback, devices=None, raw=False, iface=0, reset_timeout=30,
    reset_deadtime=300):
    """Listen for BLE advertising packets from Ruuvitags.

    Args:
        callback: Function which will be called for each received
            Ruuvitag packet.
        devices: List of BT address strings in format "fe:ed:de:ad:be:ef"
            for whitelisting devices. If None, no address filtering is made.
        raw: If False, callback is called with a dictionary with decoded
            values from advertising message, plus "time" and "rssi" keys
            which have the packet arrival time and rssi as values.
            If True, callback is called with a tuple (value, addr, rssi)
            with the value being the raw BLE packet data, addr the BT address
            of the sending device and rssi the received signal strength
            indicator from the BT stack.
        iface: The number part of the BT interface device (0 for
            /dev/hci0 etc.)
        reset_timeout: Time in seconds, after which a reset of the BT
            adapter is made, if no packets are received.
        reset_deadtime: Time in seconds. If a BT reset is made and packets
            are still not arriving, the next reset attempt is made after
            this time has passed.
    """
    if devices:
        dev = [ s.lower() for s in devices ]
        devices = dev

    recv_event = threading.Event()

    reset_thread = threading.Thread(target=idlereset,
        args=(recv_event, reset_timeout, reset_deadtime))
    reset_thread.daemon = True
    reset_thread.start()

    # Start scanning
    scanner = Scanner(iface).withDelegate(
        ScanDelegate(recv_event, callback, devices, raw))
    scanner.clear()
    scanner.start(passive=True)
    try:
        while True:
            try:
                scanner.process(0)
            except BTLEException:
                try:
                    scanner.stop()
                except BTLEException:
                    scanner._stopHelper()
                    reset_btadapter()
                scanner.clear()
                scanner.start(passive=True)
    except (KeyboardInterrupt, SystemExit):
        pass

    log.info("Stopping scan.")
    scanner.stop()
