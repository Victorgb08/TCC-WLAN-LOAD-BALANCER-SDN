import sys
import random

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController
from mn_wifi.node import OVSKernelAP
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference

N_HOSTS_AP1 = 5  # Número de hosts conectados ao AP1
N_HOSTS_AP2 = 10  # Número de hosts conectados ao AP2
MAPPINGS_FILE_PATH = "mappings.txt"  # Caminho para o arquivo de mapeamento

class Host:
    """Classe para representar um host na topologia."""
    def __init__(self, name, mac, ip):
        self.name = name
        self.mac = mac
        self.ip = ip

def create_hosts(n_hosts, start_index=1):
    """Cria uma lista de hosts com nomes, MACs e IPs únicos."""
    hosts_info = []
    for i in range(n_hosts):
        Nsta = start_index + i
        NIP = start_index + i + 1
        Nmac = start_index + i + 1
        host = Host(
            f'sta{Nsta}',
            f'00:00:00:00:00:{str(Nmac).rjust(2, "0")}',
            f'10.0.0.{NIP}/8'
        )
        hosts_info.append(host)
    return hosts_info

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
    ap1 = net.addAccessPoint('ap1', ssid='ssid-ap1', channel='1', mode='g', position='30,30,0', range=50)
    ap2 = net.addAccessPoint('ap2', ssid='ssid-ap2', channel='6', mode='g', position='70,30,0', range=50)

    c1 = net.addController('c1')

    info("*** Adicionando estações à topologia\n")
    server = net.addHost('server', mac='00:00:00:00:00:01', ip='10.0.0.1/8')

    random.seed(1)
    hosts_ap1 = create_hosts(N_HOSTS_AP1, start_index=1)
    hosts_ap2 = create_hosts(N_HOSTS_AP2, start_index=N_HOSTS_AP1 + 1)

    with open(MAPPINGS_FILE_PATH, "w") as f:
        # Adiciona hosts conectados ao AP1
        for host in hosts_ap1:
            sta_x = random.randint(20, 40)  # Posição próxima ao AP1
            sta_y = random.randint(20, 40)
            sta = net.addStation(
                host.name,
                mac=host.mac,
                ip=host.ip,
                position=f'{sta_x},{sta_y},0',
                range=13
            )
            f.write(f"{host.name} {host.mac} {host.ip}\n")

        # Adiciona hosts conectados ao AP2
        for host in hosts_ap2:
            sta_x = random.randint(60, 80)  # Posição próxima ao AP2
            sta_y = random.randint(20, 40)
            sta = net.addStation(
                host.name,
                mac=host.mac,
                ip=host.ip,
                position=f'{sta_x},{sta_y},0',
                range=13
            )
            f.write(f"{host.name} {host.mac} {host.ip}\n")

    net.setPropagationModel(model="logDistance", exp=5.5)

    info("*** Configurando nós WiFi\n")
    net.configureWifiNodes()

    info("*** Criando links\n")
    net.addLink(ap1, ap2)

    net.addLink(server, ap1)
    net.addLink(server, ap2)

    net.plotGraph(min_x=0, max_x=100, min_y=0, max_y=100)

    info("*** Iniciando a rede\n")
    net.build()
    c1.start()
    ap1.start([c1])
    ap2.start([c1])

    info("*** Executando CLI\n")
    CLI(net)

    info("*** Parando a rede\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()