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

N_HOSTS = 18  # Número de hosts
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
    """Adiciona os APs à rede em uma configuração compacta."""
    aps = []
    positions = [
        (30, 20), (50, 20), (40, 40)  # Posições próximas para sobreposição de sinais
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
            range=30  # Aumenta o alcance para permitir sobreposição
        )
        ap.setPosition(f'{pos[0]},{pos[1]},0')  # Define explicitamente a posição do AP
        aps.append(ap)
        ap_positions[ap_name] = pos  # Mapeia o nome do AP para sua posição
    return aps, ap_positions

def topology():
    """Criação da topologia com baixa densidade de APs."""
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

    with open(MAPPINGS_FILE_PATH, "w") as f:
        for i, host in enumerate(hosts_info):
            # Posiciona as estações dentro da área coberta pelos APs
            ap_index = i % len(aps)  # Distribui os hosts entre os APs
            ap_name = f'ap{ap_index + 1}'  # Nome do AP correspondente
            ap_x, ap_y = ap_positions[ap_name]  # Obtém a posição do AP

            # Posiciona os hosts próximos ao AP correspondente
            sta_x = random.randint(int(ap_x - 5), int(ap_x + 5))
            sta_y = random.randint(int(ap_y - 5), int(ap_y + 5))
            sta = net.addStation(
                host.name,
                mac=host.mac,
                ip=host.ip,
                position=f'{sta_x},{sta_y},0',
                range=13  # Reduz o alcance das estações para simular mobilidade
            )
            f.write(f"{host.name} {host.mac} {host.ip}\n")
            hosts_array.append(sta)

    net.setPropagationModel(model="logDistance", exp=5.5)  # Reduz o expoente para sinais mais fortes

    info("*** Configurando nós WiFi\n")
    net.configureWifiNodes()

    info("*** Criando links\n")
    # Conecta os APs em uma topologia triangular
    net.addLink(aps[0], aps[1])
    net.addLink(aps[1], aps[2])
    net.addLink(aps[2], aps[0])

    # Conecta o servidor a todos os APs
    for ap in aps:
        net.addLink(server, ap, cls=TCLink, bw=20)

    net.plotGraph(min_x=0, max_x=90, min_y=0, max_y=90)

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