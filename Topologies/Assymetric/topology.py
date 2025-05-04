import sys
import random

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController
from mn_wifi.node import OVSKernelAP
from mn_wifi.link import wmediumd
from mininet.link import TCLink
from mn_wifi.wmediumdConnector import interference

N_HOSTS = 24  # Número total de hosts
MAPPINGS_FILE_PATH = "mappings.txt"  # Caminho para o arquivo de mapeamento

class Host:
    """Classe para representar um host na topologia."""
    def __init__(self, name, mac, ip):
        self.name = name
        self.mac = mac
        self.ip = ip

def create_hosts(n_hosts):
    """Cria uma lista de hosts com nomes, MACs e IPs únicos."""
    hosts_info = []
    for i in range(n_hosts):
        Nsta = i + 1
        NIP = i + 2
        Nmac = i + 2
        host = Host(
            f'sta{Nsta}',
            f'00:00:00:00:00:{str(Nmac).rjust(2, "0")}',
            f'10.0.0.{NIP}/8'
        )
        hosts_info.append(host)
    return hosts_info

def add_aps(net):
    """Adiciona os APs à rede em posições mais próximas para facilitar o handover."""
    aps = []
    positions = [
        (20, 20),  # AP1
        (40, 20),  # AP2
        (60, 20),  # AP3
        (30, 40),  # AP4
        (50, 40),  # AP5
        (40, 60)   # AP6
    ]
    channels = [1, 6, 11]  # Canais para minimizar interferência

    ap_positions = {}  # Dicionário para mapear APs e suas posições

    for i, pos in enumerate(positions):
        ap_name = f'ap{i + 1}'
        ssid = f'ssid-{ap_name}'
        channel = channels[i % len(channels)]
        ap = net.addAccessPoint(
            ap_name,
            ssid=ssid,
            channel=str(channel),
            mode='g',
            range=30
        )
        ap.setPosition(f'{pos[0]},{pos[1]},0')  # Define explicitamente a posição do AP
        aps.append(ap)
        ap_positions[ap_name] = pos  # Mapeia o nome do AP para sua posição
    return aps, ap_positions

def topology():
    """Criação da topologia assimétrica."""
    info("*** Criando a rede\n")
    net = Mininet_wifi(
        controller=RemoteController,
        accessPoint=OVSKernelAP,
        link=wmediumd,
        wmediumd_mode=interference
    )

    info("*** Adicionando APs e controladores\n")
    aps, ap_positions = add_aps(net)
    c1 = net.addController('c1', controller=RemoteController)

    info("*** Adicionando estações à topologia\n")
    server = net.addHost('server', mac='00:00:00:00:00:01', ip='10.0.0.1/8')

    random.seed(1)
    hosts_info = create_hosts(N_HOSTS)
    hosts_array = []

    # Distribuição assimétrica de hosts
    host_distribution = {
        "ap1": 10,  # Alta densidade
        "ap2": 6,   # Média densidade
        "ap3": 4,   # Baixa densidade
        "ap4": 2,   # Muito baixa densidade
        "ap5": 1,   # Isolado
        "ap6": 1    # Isolado
    }

    with open(MAPPINGS_FILE_PATH, "w") as f:
        host_index = 0
        for ap_name, num_hosts in host_distribution.items():
            ap_x, ap_y = ap_positions[ap_name]
            for _ in range(num_hosts):
                if host_index >= len(hosts_info):
                    break
                host = hosts_info[host_index]
                host_index += 1

                # Posiciona os hosts próximos ao AP correspondente
                sta_x = random.randint(int(ap_x - 10), int(ap_x + 10))
                sta_y = random.randint(int(ap_y - 10), int(ap_y + 10))
                sta = net.addStation(
                    host.name,
                    mac=host.mac,
                    ip=host.ip,
                    position=f'{sta_x},{sta_y},0',
                    range=13
                )
                f.write(f"{host.name} {host.mac} {host.ip}\n")
                hosts_array.append(sta)

    net.setPropagationModel(model="logDistance", exp=5.5)

    info("*** Configurando nós WiFi\n")
    net.configureWifiNodes()

    info("*** Criando links entre APs\n")
    net.addLink(aps[0], aps[1])
    net.addLink(aps[1], aps[2])
    net.addLink(aps[2], aps[3])
    net.addLink(aps[3], aps[4])
    net.addLink(aps[4], aps[5])
    

    info("*** Criando links entre servidor e APs\n")
    for ap in aps:
        net.addLink(server, ap, cls=TCLink, bw=20)

    net.plotGraph(min_x=0, max_x=120, min_y=0, max_y=120)

    info("*** Iniciando a rede\n")
    net.build()
    c1.start()
    for ap in aps:
        ap.start([c1])

    info("*** Executando CLI\n")
    CLI(net)

    info("*** Parando a rede\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()