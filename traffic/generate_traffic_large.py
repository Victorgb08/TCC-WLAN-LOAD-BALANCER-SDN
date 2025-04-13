import os
import random
import time
import sys

random.seed(2)

# Define the number of hosts for each topology type
topology_hosts = {
    "assimetric": 30,
    "hd": 15,
    "high": 50,
    "large": 20,
    "ld": 30,
    "uniform": 5,
    "normal": 4
}

# Get the topology type from the command-line argument
if len(sys.argv) != 2:
    print("Usage: python3 generate_traffic_large.py <topology>")
    sys.exit(1)

topology = sys.argv[1]
if topology not in topology_hosts:
    print(f"Invalid topology '{topology}'. Valid options are: {', '.join(topology_hosts.keys())}")
    sys.exit(1)

N_hosts = topology_hosts[topology]
output_file = f"app_{topology}_server_output.txt"

# Start the iperf server
os.system(f'./m server iperf -s -u -p 8 -i 1 > {output_file} &')

# Generate traffic for each host
for i in range(N_hosts):
    Nsta = i + 1
    traffic = random.uniform(1, 5)  # Generate random traffic between 1 Mbps and 5 Mbps
    os.system(f'./m sta{Nsta} iperf -c 10.0.0.1 -u -p 8 -b {traffic:.2f}m -t 120 &')

# Wait for the traffic to finish
time.sleep(130)