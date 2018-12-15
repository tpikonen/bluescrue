import threading, queue, time, logging
from bluescrue import scan
from influxdb import InfluxDBClient

logging.basicConfig(level=logging.INFO,
    format="[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

log = logging.getLogger(__name__)

# The devices we're searching for
devices = [
    "fa:f5:04:eb:29:62",
#    "d6:25:60:45:b3:92",
];

## Influxdb interfacing

#def post_to_ifdb(decoded):
#    intime = int(decoded["time"]*1e9)
#    decoded.pop("time")
#    json_body = [
#    {
#        "measurement": "ruuvi_measurements",
#        "tags": {},
#        "time": intime,
#        "fields": decoded,
#    }]
#    ifclient.write_points(json_body)
##    print("wrote")


def influx_poster(client, q):
    """Post items obtained from queue to Influxdb."""
    while True:
        json_body = []
        try:
            while True:
                m = q.get_nowait()
                intime = int(m["time"]*1e9)
                m.pop("time")
                json_body.append({
                    "measurement": "ruuvi_measurements",
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
                    log.info("Posted %d points." % (len(json_body)))
                    break
                except InfluxDBServerError as e:
                    retries += 1
                    log.error("InfluxDBServerError: %s" % (e.args))
                    log.error("Retrying (%d)..." % (r))
                    time.sleep(1)
            if r >= retries:
                log.error("Failed to post to InfluxDB after %d retries, data will be discarded." % r)
        time.sleep(10)

# InfluxDB connection
ifclient = InfluxDBClient(host="localhost", port=8086, database="ruuvi")

ifq = queue.Queue()

if_thread = threading.Thread(target=influx_poster, args=(ifclient, ifq))
if_thread.daemon = True
if_thread.start()

def callback(decoded):
    ifq.put(decoded)

log.info("Influxposter starting.")
scan(callback, devices)
