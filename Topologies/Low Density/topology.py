import sys
import random

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController
from mn_wifi.node import OVSKernelAP
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference

N_HOSTS = 10  # Número de hosts
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

def topology():
    """Criação da topologia com densidade baixa."""
    info("*** Criando a rede\n")
    net = Mininet_wifi(
        controller=RemoteController,
        accessPoint=OVSKernelAP,
        link=wmediumd,
        wmediumd_mode=interference
    )

    info("*** Adicionando APs e controladores\n")
    ap1 = net.addAccessPoint('ap1', ssid='ssid-ap1', channel='1', mode='g', position='30,30,0', range=30)
    ap2 = net.addAccessPoint('ap2', ssid='ssid-ap2', channel='6', mode='g', position='70,30,0', range=30)

    c1 = net.addController('c1', controller=RemoteController)

    info("*** Adicionando estações à topologia\n")
    server = net.addHost('server', mac='00:00:00:00:00:01', ip='10.0.0.1/8')

    random.seed(1)
    hosts_info = create_hosts(N_HOSTS)
    hosts_array = []

    with open(MAPPINGS_FILE_PATH, "w") as f:
        for host in hosts_info:
            # Posiciona as estações dentro da área coberta pelos APs
            sta_x = random.randint(30, 70)
            sta_y = random.randint(20, 40)
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