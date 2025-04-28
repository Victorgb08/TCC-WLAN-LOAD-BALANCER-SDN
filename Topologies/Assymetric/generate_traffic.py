import os
import time

N_HOSTS = 24  # Número total de estações

# Inicia o servidor iperf no host 'server' com saída em formato CSV
os.system('./m server iperf -s -u -p 8 -i 1 -y C > server_output.csv &')

# Divisão das estações em grupos de tráfego
high_traffic = range(1, 10)  # Estações 1 a 6 (tráfego alto)
medium_traffic = range(10, 18)  # Estações 7 a 12 (tráfego médio)
low_traffic = range(18, 25)  # Estações 13 a 18 (tráfego baixo)

# Gera tráfego para o grupo de tráfego alto
for i in high_traffic:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 2m -t 120 &')  # 10 Mbps

# Gera tráfego para o grupo de tráfego médio
for i in medium_traffic:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 5m -t 120 &')  # 5 Mbps

# Gera tráfego para o grupo de tráfego baixo
for i in low_traffic:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 10m -t 120 &')  # 2 Mbps

# Aguarda o término do tráfego
time.sleep(130)