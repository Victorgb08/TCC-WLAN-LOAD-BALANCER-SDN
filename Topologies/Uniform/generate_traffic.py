import os
import time

N_HOSTS = 5  # Número total de estações

# Inicia o servidor iperf no host 'server' com saída em formato CSV
os.system('./m server iperf -s -u -p 8 -i 1 -y C > server_output_uniform.csv &')

# Divisão das estações em grupos de tráfego
high_traffic = range(1, 3)  # Estações 1 e 2 (tráfego alto)
medium_traffic = range(3, 5)  # Estações 3 e 4 (tráfego médio)
low_traffic = range(5, 6)  # Estação 5 (tráfego baixo)

# Gera tráfego para o grupo de tráfego alto
for i in high_traffic:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 10m -t 120 &')  # 10 Mbps

# Gera tráfego para o grupo de tráfego médio
for i in medium_traffic:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 5m -t 120 &')  # 5 Mbps

# Gera tráfego para o grupo de tráfego baixo
for i in low_traffic:
    os.system(f'./m sta{i} iperf -c 10.0.0.1 -u -p 8 -b 2m -t 120 &')  # 2 Mbps

# Aguarda o término do tráfego
time.sleep(130)