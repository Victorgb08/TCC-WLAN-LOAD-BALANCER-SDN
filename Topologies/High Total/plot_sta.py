import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Verificar se o nome do arquivo foi passado como argumento
if len(sys.argv) < 2:
    print("Uso: python plot_sta.py <nome_do_arquivo>")
    exit()

# Nome do arquivo para salvar os gráficos
file_name = sys.argv[1]

# Criar a pasta "results" se não existir
output_dir = "results"
os.makedirs(output_dir, exist_ok=True)

# Caminho do arquivo CSV
file_path = f"{file_name}.csv"

# Tentar carregar o arquivo como um DataFrame
try:
    # Carregar o arquivo CSV, ignorando a primeira linha (comando do iperf)
    data = pd.read_csv(file_path, skiprows=1, header=None)
    # Renomear as colunas com base no formato do iperf CSV
    data.columns = [
        "timestamp", "src_ip", "src_port", "dst_ip", "dst_port", "id", "interval",
        "transfer_bytes", "bandwidth_bps", "jitter_ms", "lost_packets", "total_packets",
        "loss_percentage", "out_of_order"
    ]
except Exception as e:
    print(f"Erro ao carregar o arquivo: {e}")
    exit()

# Converter colunas numéricas para o tipo correto
numeric_columns = [
    "transfer_bytes", "bandwidth_bps", "jitter_ms", "lost_packets",
    "total_packets", "loss_percentage", "out_of_order"
]
data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, errors='coerce')

# Converter o timestamp para um formato legível
data['timestamp'] = pd.to_datetime(data['timestamp'], format='%Y%m%d%H%M%S')

# Converter largura de banda de bps para Mbps
data['bandwidth_mbps'] = data['bandwidth_bps'] / 1_000_000

# Ordenar os IPs em ordem crescente e criar o mapeamento para sta{x-1}
sorted_ips = sorted(data['src_ip'].unique())
ip_to_sta = {ip: f"sta{int(ip.split('.')[-1]) - 1}" for ip in sorted_ips}
print(ip_to_sta)

# Substituir os IPs pelos nomes das estações no DataFrame
data['station'] = data['src_ip'].map(ip_to_sta)

# Exibir informações básicas para depuração
print("Dados carregados:")
print(data.head())
print("\nColunas disponíveis:")
print(data.columns)
print("\nEstatísticas de largura de banda (Mbps):")
print(data['bandwidth_mbps'].describe())

# Criar um único gráfico com todas as estações (largura de banda)
plt.figure(figsize=(12, 8))

for station in data['station'].unique():
    subset = data[data['station'] == station]
    sns.lineplot(data=subset, x="timestamp", y="bandwidth_mbps", label=station, marker='o')

# Configurar o gráfico de largura de banda
plt.title("Largura de Banda ao Longo do Tempo - Todas as Estações")
plt.xlabel("Tempo")
plt.ylabel("Largura de Banda (Mbps)")
plt.legend(title="Estação", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
plt.grid(True)
plt.tight_layout()

# Salvar o gráfico de largura de banda
bandwidth_plot_path = os.path.join(output_dir, f"{file_name}_bandwidth.png")
plt.savefig(bandwidth_plot_path, bbox_inches='tight')
print(f"Gráfico de largura de banda salvo em: {bandwidth_plot_path}")
plt.close()

# Criar um gráfico de perda de pacotes por host
plt.figure(figsize=(12, 8))

for station in data['station'].unique():
    subset = data[data['station'] == station]
    sns.lineplot(data=subset, x="timestamp", y="loss_percentage", label=station, marker='o')

# Configurar o gráfico de perda de pacotes
plt.title("Perda de Pacotes ao Longo do Tempo - Todas as Estações")
plt.xlabel("Tempo")
plt.ylabel("Perda de Pacotes (%)")
plt.legend(title="Estação", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
plt.grid(True)
plt.tight_layout()

# Salvar o gráfico de perda de pacotes
loss_plot_path = os.path.join(output_dir, f"{file_name}_loss.png")
plt.savefig(loss_plot_path, bbox_inches='tight')
print(f"Gráfico de perda de pacotes salvo em: {loss_plot_path}")
plt.close()