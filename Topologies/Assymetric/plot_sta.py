import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Caminho do arquivo CSV
file_path = "server_output.csv"

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

# Exibir informações básicas para depuração
print("Dados carregados:")
print(data.head())
print("\nColunas disponíveis:")
print(data.columns)
print("\nEstatísticas de largura de banda (Mbps):")
print(data['bandwidth_mbps'].describe())

# Criar um único gráfico com todas as estações
plt.figure(figsize=(12, 8))
unique_src_ips = data['src_ip'].unique()

for src_ip in unique_src_ips:
    subset = data[data['src_ip'] == src_ip]
    sns.lineplot(data=subset, x="timestamp", y="bandwidth_mbps", label=src_ip, marker='o')

# Configurar o gráfico
plt.title("Largura de Banda ao Longo do Tempo - Todas as Estações")
plt.xlabel("Tempo")
plt.ylabel("Largura de Banda (Mbps)")
plt.legend(title="Estação (src_ip)")
plt.grid(True)
plt.tight_layout()
plt.show()