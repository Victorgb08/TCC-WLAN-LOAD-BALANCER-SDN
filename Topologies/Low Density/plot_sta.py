import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Caminhos dos arquivos de entrada
files = ["server_output_nolb.csv", "server_output_nc.csv", "server_output_load.csv"]
labels = ["nolb", "nc", "load"]

# Criar a pasta "results" se não existir
output_dir = "results"
os.makedirs(output_dir, exist_ok=True)

# Função para processar um arquivo e gerar gráficos
def process_and_plot(file_path, label):
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
        print(f"Erro ao carregar o arquivo {file_path}: {e}")
        return

    # Converter colunas numéricas para o tipo correto
    numeric_columns = [
        "transfer_bytes", "bandwidth_bps", "jitter_ms", "lost_packets",
        "total_packets", "loss_percentage", "out_of_order"
    ]
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # Converter o timestamp para um formato legível
    data['timestamp'] = pd.to_datetime(data['timestamp'], format='%Y%m%d%H%M%S')

    # Ajustar o eixo X para começar em 0
    data['time_since_start'] = (data['timestamp'] - data['timestamp'].iloc[0]).dt.total_seconds()

    # Converter largura de banda de bps para Mbps
    data['bandwidth_mbps'] = data['bandwidth_bps'] / 1_000_000

    # Ordenar os IPs em ordem crescente e criar o mapeamento para sta1, sta2, ...
    sorted_ips = sorted(data['src_ip'].unique())
    ip_to_sta = {ip: f"sta{i+1}" for i, ip in enumerate(sorted_ips)}

    # Substituir os IPs pelos nomes das estações no DataFrame
    data['station'] = data['src_ip'].map(ip_to_sta)

    # Criar um único gráfico com todas as estações (largura de banda)
    plt.figure(figsize=(12, 8))

    for station in data['station'].unique():
        subset = data[data['station'] == station]
        sns.lineplot(data=subset, x="time_since_start", y="bandwidth_mbps", label=station, marker='o')

    # Configurar o gráfico de largura de banda
    plt.title(f"Largura de Banda ao Longo do Tempo", fontsize=20)
    plt.xlabel("Tempo (s)", fontsize=16)
    plt.ylabel("Largura de Banda (Mbps)", fontsize=16)
    plt.xticks(ticks=range(0, int(data['time_since_start'].max()) + 1, 5), fontsize=12)  # Incrementos de 5 segundos
    plt.yticks(fontsize=12)
    plt.legend(title="Estação", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
    plt.grid(True)
    plt.tight_layout()

    # Salvar o gráfico de largura de banda
    bandwidth_plot_path = os.path.join(output_dir, f"server_output_{label.replace(' ', '_').lower()}_bandwidth.png")
    plt.savefig(bandwidth_plot_path, bbox_inches='tight')
    print(f"Gráfico de largura de banda salvo em: {bandwidth_plot_path}")
    plt.close()

    # Criar um gráfico de perda de pacotes por host
    plt.figure(figsize=(12, 8))

    for station in data['station'].unique():
        subset = data[data['station'] == station]
        sns.lineplot(data=subset, x="time_since_start", y="loss_percentage", label=station, marker='o')

    # Configurar o gráfico de perda de pacotes
    plt.title(f"Perda de Pacotes ao Longo do Tempo", fontsize=20)
    plt.xlabel("Tempo (s)", fontsize=16)
    plt.ylabel("Perda de Pacotes (%)", fontsize=16)
    plt.xticks(ticks=range(0, int(data['time_since_start'].max()) + 1, 5), fontsize=12)  # Incrementos de 5 segundos
    plt.yticks(fontsize=12)
    plt.legend(title="Estação", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
    plt.grid(True)
    plt.tight_layout()

    # Salvar o gráfico de perda de pacotes
    loss_plot_path = os.path.join(output_dir, f"server_output_{label.replace(' ', '_').lower()}_loss.png")
    plt.savefig(loss_plot_path, bbox_inches='tight')
    print(f"Gráfico de perda de pacotes salvo em: {loss_plot_path}")
    plt.close()

# Processar todos os arquivos e gerar gráficos
for file, label in zip(files, labels):
    process_and_plot(file, label)