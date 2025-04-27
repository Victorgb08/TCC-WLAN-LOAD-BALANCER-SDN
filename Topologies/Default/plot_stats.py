import pandas as pd
import os

# Caminhos dos arquivos de entrada
files = ["server_output_nolb.csv", "server_output_nc.csv", "server_output_load.csv"]
labels = ["No Load Balancer", "With NC", "With Load Balancer"]

# Caminho do arquivo de saída
output_dir = "Resultados"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "stats.txt")

# Função para processar um arquivo e calcular métricas
def process_file(file_path, label):
    if not os.path.exists(file_path):
        print(f"Erro: Arquivo {file_path} não encontrado.")
        return None

    try:
        data = pd.read_csv(file_path, skiprows=1, header=None)
        data.columns = [
            "timestamp", "src_ip", "src_port", "dst_ip", "dst_port", "id", "interval",
            "transfer_bytes", "bandwidth_bps", "jitter_ms", "lost_packets", "total_packets",
            "loss_percentage", "out_of_order"
        ]
    except Exception as e:
        print(f"Erro ao carregar o arquivo {file_path}: {e}")
        return None

    # Converter colunas numéricas para o tipo correto
    numeric_columns = [
        "transfer_bytes", "bandwidth_bps", "jitter_ms", "lost_packets",
        "total_packets", "loss_percentage", "out_of_order"
    ]
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # Converter largura de banda de bps para Mbps
    data['bandwidth_mbps'] = data['bandwidth_bps'] / 1_000_000

    # Calcular métricas por host
    metrics = data.groupby("src_ip").agg(
        avg_bandwidth_mbps=("bandwidth_mbps", "mean"),
        avg_loss_percentage=("loss_percentage", "mean")
    ).reset_index()

    return label, metrics

# Processar todos os arquivos e consolidar as métricas
all_metrics = []
for file, label in zip(files, labels):
    result = process_file(file, label)
    if result:
        all_metrics.append(result)

# Salvar as métricas no arquivo stats.txt
try:
    with open(output_file, "w") as f:
        for label, metrics in all_metrics:
            f.write(f"=== Estatísticas para {label} ===\n")
            for _, row in metrics.iterrows():
                f.write(f"Host: {row['src_ip']}\n")
                f.write(f"  Média de Vazão (Mbps): {row['avg_bandwidth_mbps']:.2f}\n")
                f.write(f"  Média de Perda de Pacotes (%): {row['avg_loss_percentage']:.2f}\n")
                f.write("\n")
        print(f"Estatísticas salvas em: {output_file}")
except Exception as e:
    print(f"Erro ao salvar o arquivo {output_file}: {e}")
    exit()