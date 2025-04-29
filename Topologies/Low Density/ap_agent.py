import subprocess
import redis
import threading
import time
import pickle
import re

# APs
aps = ['ap1', 'ap2', 'ap3']

stations_mapping = {}
stations_aps = {}
stations_traffic = {}
ap_metrics = []

mappings_path = "mappings.txt"
AP_METRICS_PERIOD_IN_SECONDS = 10
REDIS_UPDATE_PERIOD_IN_SECONDS = 10

# Utility functions

def read_mappings():
    with open(mappings_path) as f:
        for line in f:
            data = line.split(' ')
            stations_mapping[data[1]] = data[0]
            stations_aps[data[0]] = {}

    print('mapping', stations_mapping)
    print('aps', stations_aps)

# Execute the command
def run_cmd(cmd, timeout=15):  # Aumentado o timeout para 15 segundos
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout)
        return output.decode('UTF-8', 'ignore')
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(cmd)}")
        return None
    except subprocess.CalledProcessError as ex:
        if ex.returncode == 255:
            print(f"Warning: {ex.output.strip()}")
            return None
        print(f"Command execution returned exit status {ex.returncode}:\n{ex.output.strip()}")
        return None

# Parse SSID
def get_ssid(output):
    if not output:
        return None
    for line in output.split("\n"):
        if "ssid" in line:
            return line.split(' ')[1]
    return None

# Parse stations
def get_stations(output):
    if not output:
        return {}
    stations = {}
    station_pattern = re.compile(r"Station\s+([0-9a-f:]+)")
    rx_pattern = re.compile(r"rx bytes:\s+(\d+)")
    tx_pattern = re.compile(r"tx bytes:\s+(\d+)")

    curr_station = None
    for line in output.split("\n"):
        station_match = station_pattern.search(line)
        if station_match:
            curr_station = station_match.group(1)
            stations[curr_station] = {}
        elif curr_station:
            rx_match = rx_pattern.search(line)
            if rx_match:
                stations[curr_station]["rx_bytes"] = rx_match.group(1)
            tx_match = tx_pattern.search(line)
            if tx_match:
                stations[curr_station]["tx_bytes"] = tx_match.group(1)
    return stations

def get_signal_strengths(output):
    if not output:
        return {}
    signal_strengths = {}
    signal_pattern = re.compile(r"signal:\s+(-\d+)")
    ssid_pattern = re.compile(r"SSID:\s+(\S+)")

    curr_signal = None
    for line in output.split("\n"):
        signal_match = signal_pattern.search(line)
        if signal_match:
            curr_signal = signal_match.group(1)
        ssid_match = ssid_pattern.search(line)
        if ssid_match:
            ssid = ssid_match.group(1)
            signal_strengths[ssid] = curr_signal
    return signal_strengths

def calculate_bandwidth(curr_bytes, prev_bytes):
    if int(curr_bytes) < int(prev_bytes):  # Handle counter reset
        prev_bytes = 0
    return (int(curr_bytes) - int(prev_bytes)) / AP_METRICS_PERIOD_IN_SECONDS

def measures_ap_metrics():
    dpid = 1
    report = []
    for ap in aps:
        result = {"name": ap, "dpid": dpid}
        apifname = ap + "-wlan1"
        result["if_name"] = apifname

        # Get SSID
        cmd = ['iw', 'dev', apifname, 'info']
        output = run_cmd(cmd)
        result["ssid"] = get_ssid(output)

        # Get associated stations
        cmd = ['iw', 'dev', apifname, 'station', 'dump']
        output = run_cmd(cmd)
        stations_associated = get_stations(output)

        result['stations_associated'] = {}
        for station in stations_associated:
            prev_rx_bytes = stations_traffic.get(station, {}).get("rx_bytes", 0)
            prev_tx_bytes = stations_traffic.get(station, {}).get("tx_bytes", 0)

            curr_rx_bytes = stations_associated[station].get("rx_bytes", 0)
            curr_tx_bytes = stations_associated[station].get("tx_bytes", 0)

            stations_traffic[station] = {
                "rx_bytes": curr_rx_bytes,
                "tx_bytes": curr_tx_bytes
            }

            rx_bw = calculate_bandwidth(curr_rx_bytes, prev_rx_bytes)
            tx_bw = calculate_bandwidth(curr_tx_bytes, prev_tx_bytes)

            station_name = stations_mapping[station]
            result['stations_associated'][station_name] = stations_aps[station_name]
            result['stations_associated'][station_name]['rx_rate'] = rx_bw * 8 / 1_000_000  # Convert to Mbps
            result['stations_associated'][station_name]['tx_rate'] = tx_bw * 8 / 1_000_000  # Convert to Mbps

        report.append(result)
        dpid += 1

    # Print the collected statistics
    print("\n=========================== Métricas dos APs ===========================")
    for ap_stat in report:
        total_rx = 0
        total_tx = 0
        print(f"AP: {ap_stat['name']}")
        print(f"  Estações Associadas: {len(ap_stat['stations_associated'])}")
        for station_name, station_info in ap_stat['stations_associated'].items():
            rx_rate = station_info.get('rx_rate', 0)
            tx_rate = station_info.get('tx_rate', 0)
            total_rx += rx_rate
            total_tx += tx_rate
            print(f"    Estação: {station_name}")
            print(f"      Taxa de Recepção (RX): {rx_rate:.2f} Mbps")
            print(f"      Taxa de Transmissão (TX): {tx_rate:.2f} Mbps")
            print(f"      Sinal dos APs Disponíveis: {station_info.get('aps', {})}")
        print(f"  Taxa Total de Recepção (RX): {total_rx:.2f} Mbps")
        print(f"  Taxa Total de Transmissão (TX): {total_tx:.2f} Mbps")
        print("-------------------------------------------------------------------------------")
    print("===============================================================================")

    return report

class ApMetrics(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global ap_metrics
        while True:
            ap_metrics = measures_ap_metrics()
            time.sleep(AP_METRICS_PERIOD_IN_SECONDS)

class StationMetrics(threading.Thread):
    def __init__(self, station_name):
        super().__init__()
        self.station_name = station_name

    def get_ap_strengths(self, station_name):
        ssifname = station_name + "-wlan0"
        cmd = ['./m', station_name, 'iw', 'dev', ssifname, 'scan']
        output = run_cmd(cmd)
        if output:
            stations_aps[station_name] = {
                'aps': get_signal_strengths(output),
            }
        else:
            print(f"Failed to get AP strengths for {station_name}")

    def run(self):
        self.get_ap_strengths(self.station_name)

class Sender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.redis = redis.Redis('127.0.0.1')
        self.pubsub = self.redis.pubsub()

    def run(self):
        global ap_metrics
        while True:
            pvalue = pickle.dumps(ap_metrics)
            self.redis.publish("statistics", pvalue)
            time.sleep(REDIS_UPDATE_PERIOD_IN_SECONDS)

class Listener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.redis = redis.Redis('127.0.0.1')
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(['sdn'])

    def run(self):
        for item in self.pubsub.listen():
            tmp = item['data']
            if tmp == 1:
                continue
            data = pickle.loads(tmp)
            print("data received for migration ", data)
            self.migrate(data)

    def migrate(self, data):
        ifname = data['station_name'] + '-wlan0'

        cmd = ['./m', data['station_name'], 'iw', 'dev', ifname, 'disconnect']
        print(cmd)
        print(run_cmd(cmd))

        cmd = ['./m', data['station_name'], 'iw', 'dev', ifname, 'connect', data['ssid']]
        print(cmd)
        print(run_cmd(cmd))
        print()

if __name__ == '__main__':
    read_mappings()

    for station in stations_mapping:
        station_monitor = StationMetrics(stations_mapping[station])
        station_monitor.start()

    ap_monitor = ApMetrics()
    ap_monitor.start()

    sender = Sender()
    receiver = Listener()
    sender.start()
    receiver.start()