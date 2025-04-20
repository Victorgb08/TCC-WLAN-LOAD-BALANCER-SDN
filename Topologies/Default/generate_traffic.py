import os
import time

# Inicia o servidor iperf no host 'server' com saída em formato CSV
os.system('./m server iperf -s -u -p 8 -i 1 -y C > server_output.csv &')

# Lista de hosts (um host por AP)
hosts = [1, 2, 3, 4]  # sta1, sta2, sta3, sta4

# Gera tráfego para cada host
for i in hosts:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 15m -t 120 &')  # Tráfego de 8 Mbps por host

# Aguarda o término do tráfego
time.sleep(60)