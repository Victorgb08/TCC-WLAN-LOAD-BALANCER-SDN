import os
import random
import time

random.seed(2)

N_hosts = 30  # Número de hosts na topologia de densidade baixa

# Inicia o servidor iperf no host 'server'
os.system('./m server iperf -s -u -p 8 -i 1 > server_output.txt &')

# Gera tráfego para cada host
for i in range(N_hosts):
    Nsta = i + 1
    traffic = random.uniform(1, 5)  # Gera tráfego aleatório entre 1 Mbps e 5 Mbps
    os.system(f'./m sta{Nsta} iperf -c 10.0.0.1 -u -p 8 -b {traffic:.2f}m -t 120 &')

# Aguarda o término do tráfego
time.sleep(130)