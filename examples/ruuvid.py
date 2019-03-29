import threading, queue, time, logging, toml
import requests.exceptions
from bluescrue import scan
from influxdb import InfluxDBClient
from influxdb.exceptions import *

logging.basicConfig(level=logging.INFO,
    format="[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

log = logging.getLogger(__name__)


def parse_config(conffile):
    """Read configuraton from TOML file, set global vars."""
    global device_locs
    global devices
    conf = toml.load(conffile)
    device_locs = conf['devices']
    devices = device_locs.keys()

## Influxdb interfacing

def influx_poster(client, q):
    """Post items obtained from queue to Influxdb."""
    while True:
        json_body = []
        try:
            while True:
                m = q.get_nowait()
                try:
                    intime = int(m.pop("time")*1e9)
                    # Drop constant fields
                    mac = m.pop("mac")
                    m.pop("data_format")
                    m.pop("tx_power")
                except KeyError as e:
                    log.error("Key '%s' not found in decoded message." % (e.args))
                json_body.append({
                    "measurement": device_locs[mac],
                    "tags": {},
                    "time": intime,
                    "fields": m,
                })
                q.task_done()
        except queue.Empty:
            pass
        if json_body:
            retries = 5
            r = 0
            while r < retries:
                try:
                    client.write_points(json_body)
                    log.debug("Wrote %d points." % (len(json_body)))
                    break
                except (InfluxDBServerError, InfluxDBClientError) as e:
                    r += 1
                    log.warning("InfluxDB Error: %s" % (e))
                    log.warning("Retrying (%d)..." % (r))
                    time.sleep(1)
                except (requests.exceptions.ConnectionError,
                  requests.exceptions.HTTPError,
                  requests.exceptions.Timeout) as e:
                    r += 1
                    log.warning("Requests Error: %s" % (e))
                    log.warning("Retrying (%d)..." % (r))
                    time.sleep(20)
            if r > 0 and r < retries:
                log.warning("Successful write of %d points after %d retries" % (len(json_body), r))
            elif r >= retries:
                log.error("Failed InfluxDB write after %d retries, %d data points discarded." % (r, len(json_body)))
        time.sleep(10)

parse_config("ruuvid.conf")

# InfluxDB connection
ifclient = InfluxDBClient(host="localhost", port=8086, database="koti")

ifq = queue.Queue()

if_thread = threading.Thread(target=influx_poster, args=(ifclient, ifq))
if_thread.daemon = True
if_thread.start()

def callback(decoded):
    ifq.put(decoded)

log.info("RuuviD starting.")
scan(callback, devices)
