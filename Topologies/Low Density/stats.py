import pandas as pd
import ipaddress

# Lista de cenários e arquivos de entrada
scenarios = ["load", "nolb", "nc"]
input_files = [f"server_output_{scenario}.csv" for scenario in scenarios]

# Caminho do arquivo CSV de saída
output_file = "estatisticas_por_ip.csv"

# Lista para armazenar os DataFrames de cada cenário
all_stats = []

# Processar cada arquivo de entrada
for scenario, input_file in zip(scenarios, input_files):
    # Ler o arquivo CSV, ignorando a primeira linha (comando)
    data = pd.read_csv(input_file, skiprows=1, header=None)

    # Nomear as colunas do DataFrame
    data.columns = [
        "timestamp", "src_ip", "src_port", "dst_ip", "dst_port", "id", "interval",
        "transfer_bytes", "bandwidth_bps", "jitter_ms", "lost_packets", "total_packets",
        "loss_percentage", "out_of_order"
    ]

    # Converter bandwidth_bps para Mbps
    data["bandwidth_mbps"] = data["bandwidth_bps"] / 1_000_000

    # Calcular a média de vazão (bandwidth_mbps) e perda de pacotes (loss_percentage) por IP de origem (src_ip)
    stats_per_ip = data.groupby("src_ip").agg(
        mean_bandwidth_mbps=("bandwidth_mbps", "mean"),
        mean_loss_percentage=("loss_percentage", "mean")
    ).reset_index()

    # Ordenar os resultados por IP de origem (src_ip) como endereços IP numéricos
    stats_per_ip["src_ip_numeric"] = stats_per_ip["src_ip"].apply(lambda ip: int(ipaddress.IPv4Address(ip)))
    stats_per_ip = stats_per_ip.sort_values(by="src_ip_numeric").drop(columns=["src_ip_numeric"])

    # Alterar o formato do IP para sta{x-1}
    stats_per_ip["src_ip"] = stats_per_ip["src_ip"].apply(
        lambda ip: f"sta{int(ip.split('.')[-1]) - 1}"
    )

    # Limitar os resultados a 2 casas decimais
    stats_per_ip = stats_per_ip.round(2)

    # Adicionar uma coluna para identificar o cenário
    stats_per_ip["scenario"] = scenario

    # Adicionar o DataFrame do cenário à lista
    all_stats.append(stats_per_ip)

# Concatenar os resultados de todos os cenários
final_stats = pd.concat(all_stats, ignore_index=True)

# Exportar as estatísticas para um único arquivo CSV
final_stats.to_csv(output_file, index=False)

print(f"Estatísticas exportadas para o arquivo '{output_file}'.")