import pandas as pd
import os
import ipaddress

# Caminhos dos arquivos de entrada
files = ["server_output_nolb.csv", "server_output_nc.csv", "server_output_load.csv"]
labels = ["No Load Balancer", "With NC", "With Load Balancer"]

# Caminho do arquivo de saída
output_dir = "results"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "stats.txt")
latex_file = os.path.join(output_dir, "tables.tex")

# Função para mapear IPs para sta{número}
def map_ip_to_sta(ip):
    last_octet = int(ip.split(".")[-1])
    return f"sta{last_octet - 1}"  # Ajuste para mapear corretamente

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

    # Mapear IPs para sta{número}
    data['station'] = data['src_ip'].apply(map_ip_to_sta)

    # Adicionar uma coluna auxiliar para ordenação numérica dos IPs
    data['src_ip_numeric'] = data['src_ip'].apply(lambda ip: int(ipaddress.IPv4Address(ip)))

    # Calcular métricas por estação
    metrics = data.groupby(["station", "src_ip_numeric"]).agg(
        avg_bandwidth_mbps=("bandwidth_mbps", "mean"),
        avg_loss_percentage=("loss_percentage", "mean")
    ).reset_index()

    # Ordenar as métricas pela coluna numérica do IP
    metrics = metrics.sort_values(by="src_ip_numeric").drop(columns=["src_ip_numeric"])

    return label, metrics

# Processar todos os arquivos e consolidar as métricas
all_metrics = []
for file, label in zip(files, labels):
    result = process_file(file, label)
    if result:
        all_metrics.append(result)

# Função para calcular as médias globais de vazão e perda de pacotes
def calculate_global_metrics(metrics):
    """Calcula a média global de vazão e perda de pacotes."""
    avg_bandwidth_global = metrics['avg_bandwidth_mbps'].mean()
    avg_loss_global = metrics['avg_loss_percentage'].mean()
    return avg_bandwidth_global, avg_loss_global

# Processar todos os arquivos e consolidar as métricas
all_metrics = []
for file, label in zip(files, labels):
    result = process_file(file, label)
    if result:
        all_metrics.append(result)

# Salvar as métricas no arquivo stats.txt e gerar tabelas LaTeX
try:
    with open(output_file, "w") as f, open(latex_file, "w") as latex_f:
        for label, metrics in all_metrics:
            # Salvar no arquivo stats.txt
            f.write(f"=== Estatísticas para {label} ===\n")
            for _, row in metrics.iterrows():
                f.write(f"Host: {row['station']}\n")
                f.write(f"  Média de Vazão (Mbps): {row['avg_bandwidth_mbps']:.2f}\n")
                f.write(f"  Média de Perda de Pacotes (%): {row['avg_loss_percentage']:.2f}\n")
                f.write("\n")
            
            # Calcular as médias globais
            avg_bandwidth_global, avg_loss_global = calculate_global_metrics(metrics)
            f.write(f"Média Global de Vazão (Mbps): {avg_bandwidth_global:.2f}\n")
            f.write(f"Média Global de Perda de Pacotes (%): {avg_loss_global:.2f}\n")
            f.write("\n")

            # Gerar tabela LaTeX
            latex_f.write(f"\\begin{{table}}[htbp]\n")
            latex_f.write(f"    \\centering\n")
            latex_f.write(f"    \\begin{{tabular}}{{|c|>{{\\centering\\arraybackslash}}p{{4cm}}|>{{\\centering\\arraybackslash}}p{{4cm}}|>{{\\centering\\arraybackslash}}p{{4cm}}|}}\n")
            latex_f.write(f"        \\hline\n")
            latex_f.write(f"        \\textbf{{Host}} & \\textbf{{Média de Vazão (Mbps)}} & \\textbf{{Média de Perda de Pacotes (\\%)}} & \\textbf{{Tráfego gerado (Mbps)}} \\\\ \\hline\n")
            
            # Adicionar as linhas da tabela
            for _, row in metrics.iterrows():
                # Definir o tráfego gerado (exemplo: baseado em uma lógica fixa ou calculada)
                if "sta1" <= row['station'] <= "sta6":
                    traffic_generated = 10
                elif "sta7" <= row['station'] <= "sta12":
                    traffic_generated = 10
                else:
                    traffic_generated = 10
                
                latex_f.write(f"        {row['station']} & {row['avg_bandwidth_mbps']:.2f} & {row['avg_loss_percentage']:.2f} & {traffic_generated} \\\\ \\hline\n")
            
            latex_f.write(f"    \\end{{tabular}}\n")
            latex_f.write(f"    \\caption{{Estatísticas de desempenho para o cenário {label.lower()}.}}\n")
            latex_f.write(f"\\end{{table}}\n\n")

        print(f"Estatísticas salvas em: {output_file}")
        print(f"Tabelas LaTeX salvas em: {latex_file}")
except Exception as e:
    print(f"Erro ao salvar os arquivos: {e}")
    exit()
