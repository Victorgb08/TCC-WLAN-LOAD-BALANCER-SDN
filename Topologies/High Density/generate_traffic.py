import os
import time

N_HOSTS = 9  # Número total de estações

# Inicia o servidor iperf no host 'server' com saída em formato CSV
os.system('./m server iperf -s -u -p 8 -i 1 -y C > server_output_hd.csv &')

# Divisão das estações em grupos de tráfego
high_traffic = range(1, 4)  # Estações 1 a 3 (tráfego alto)
medium_traffic = range(4, 7)  # Estações 4 a 6 (tráfego médio)
low_traffic = range(7, 10)  # Estações 7 a 9 (tráfego baixo)

# Gera tráfego para o grupo de tráfego alto
for i in high_traffic:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 8m -t 120 &')  # 10 Mbps

# Gera tráfego para o grupo de tráfego médio
for i in medium_traffic:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 5m -t 120 &')  # 5 Mbps

# Gera tráfego para o grupo de tráfego baixo
for i in low_traffic:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 2m -t 120 &')  # 2 Mbps

# Aguarda o término do tráfego
time.sleep(130)