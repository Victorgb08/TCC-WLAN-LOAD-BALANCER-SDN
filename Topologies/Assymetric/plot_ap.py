import json
import matplotlib.pyplot as plt
from datetime import datetime

# Nome do arquivo JSON exportado
JSON_FILE = "ap_metrics.json"

def load_metrics():
    """Carrega os dados do arquivo JSON."""
    try:
        with open(JSON_FILE, "r") as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Erro ao carregar o arquivo {JSON_FILE}. Verifique se ele existe e está no formato correto.")
        return []

def process_metrics(data):
    """Processa os dados do JSON para agrupar informações por AP."""
    ap_data = {}
    for entry in data:
        ap_name = entry["name"]
        timestamp = datetime.fromisoformat(entry["timestamp"])
        total_rx_rate = sum(station["rx_rate"] for station in entry["stations_associated"].values())
        total_tx_rate = sum(station["tx_rate"] for station in entry["stations_associated"].values())

        if ap_name not in ap_data:
            ap_data[ap_name] = {"timestamps": [], "rx_rates": [], "tx_rates": []}

        ap_data[ap_name]["timestamps"].append(timestamp)
        ap_data[ap_name]["rx_rates"].append(total_rx_rate)
        ap_data[ap_name]["tx_rates"].append(total_tx_rate)

    return ap_data

def plot_ap_metrics(ap_data):
    """Plota as informações gerais dos APs ao longo do tempo."""
    if not ap_data:
        print("Nenhum dado disponível para plotar.")
        return

    plt.figure(figsize=(12, 6))

    # Gráfico de RX Rate
    plt.subplot(2, 1, 1)
    for ap_name, data in ap_data.items():
        plt.plot(data["timestamps"], data["rx_rates"], label=f"{ap_name} RX Rate")
    plt.title("Taxa de Recepção (RX Rate) dos APs ao longo do tempo")
    plt.xlabel("Tempo")
    plt.ylabel("RX Rate (Mbps)")
    plt.legend()
    plt.grid()

    # Gráfico de TX Rate
    plt.subplot(2, 1, 2)
    for ap_name, data in ap_data.items():
        plt.plot(data["timestamps"], data["tx_rates"], label=f"{ap_name} TX Rate")
    plt.title("Taxa de Transmissão (TX Rate) dos APs ao longo do tempo")
    plt.xlabel("Tempo")
    plt.ylabel("TX Rate (Mbps)")
    plt.legend()
    plt.grid()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Carregar os dados do JSON
    metrics_data = load_metrics()

    # Processar os dados
    ap_data = process_metrics(metrics_data)

    # Plotar os gráficos
    plot_ap_metrics(ap_data)