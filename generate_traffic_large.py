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

# Check if the script 'm' exists and is executable
if not os.path.isfile('./m') or not os.access('./m', os.X_OK):
    print("Error: The script './m' is not found or not executable.")
    sys.exit(1)

# Get the topology type and optional bandwidth range from the command-line arguments
if len(sys.argv) < 2:
    print("Usage: python3 generate_traffic_large.py <topology> [min_bandwidth] [max_bandwidth]")
    sys.exit(1)

topology = sys.argv[1]
if topology not in topology_hosts:
    print(f"Invalid topology '{topology}'. Valid options are: {', '.join(topology_hosts.keys())}")
    sys.exit(1)

min_bandwidth = float(sys.argv[2]) if len(sys.argv) > 2 else 1
max_bandwidth = float(sys.argv[3]) if len(sys.argv) > 3 else 5

N_hosts = topology_hosts[topology]
output_file = f"app_{topology}_server_output.txt"
traffic_duration = 120  # Duration of traffic in seconds
wait_time = traffic_duration + 10  # Wait time to ensure traffic finishes

print(f"Starting traffic generation for topology: {topology}")
print(f"Number of hosts: {N_hosts}")
print(f"Output file: {output_file}")
print(f"Bandwidth range: {min_bandwidth} Mbps to {max_bandwidth} Mbps")

# Start the iperf server
server_command = f'./m server iperf -s -u -p 8 -i 1 > {output_file} &'
if os.system(server_command) != 0:
    print("Error: Failed to start iperf server.")
    sys.exit(1)

# Generate traffic for each host
for i in range(N_hosts):
    Nsta = i + 1
    traffic = random.uniform(min_bandwidth, max_bandwidth)
    client_command = f'./m sta{Nsta} iperf -c 10.0.0.1 -u -p 8 -b {traffic:.2f}m -t {traffic_duration} &'
    if os.system(client_command) != 0:
        print(f"Error: Failed to start iperf client for sta{Nsta}.")

# Wait for the traffic to finish
time.sleep(wait_time)

# Stop the iperf server
os.system("pkill -f 'iperf -s -u'")
print("Traffic generation completed.")