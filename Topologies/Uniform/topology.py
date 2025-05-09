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

N_HOSTS = 6  # Número de hosts
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
    """Criação da topologia uniforme."""
    info("*** Criando a rede\n")
    net = Mininet_wifi(
        controller=RemoteController,
        accessPoint=OVSKernelAP,
        link=wmediumd,
        wmediumd_mode=interference
    )

    info("*** Adicionando APs e controladores\n")
    ap1 = net.addAccessPoint('ap1', ssid='ssid-ap1', channel='1', mode='g', position='20,30,0', range=40, txpower=20)
    ap2 = net.addAccessPoint('ap2', ssid='ssid-ap2', channel='6', mode='g', position='40,30,0', range=40, txpower=20)
    ap3 = net.addAccessPoint('ap3', ssid='ssid-ap3', channel='11', mode='g', position='60,30,0', range=40, txpower=20)
    ap4 = net.addAccessPoint('ap4', ssid='ssid-ap4', channel='1', mode='g', position='20,60,0', range=40, txpower=20)
    ap5 = net.addAccessPoint('ap5', ssid='ssid-ap5', channel='6', mode='g', position='40,60,0', range=40, txpower=20)
    ap6 = net.addAccessPoint('ap6', ssid='ssid-ap6', channel='11', mode='g', position='60,60,0', range=40, txpower=20)

    c1 = net.addController('c1', controller=RemoteController)

    info("*** Adicionando estações à topologia\n")
    server = net.addHost('server', mac='00:00:00:00:00:01', ip='10.0.0.1/8')

    random.seed(1)
    hosts_info = create_hosts(N_HOSTS)
    hosts_array = []

    with open(MAPPINGS_FILE_PATH, "w") as f:
        for i, host in enumerate(hosts_info):
            # Posiciona cada estação próxima ao AP correspondente
            if i == 0:
                sta_x, sta_y = 20, 30  # Próximo ao AP1
            elif i == 1:
                sta_x, sta_y = 40, 30  # Próximo ao AP2
            elif i == 2:
                sta_x, sta_y = 60, 30  # Próximo ao AP3
            elif i == 3:
                sta_x, sta_y = 20, 60  # Próximo ao AP4
            elif i == 4:
                sta_x, sta_y = 40, 60  # Próximo ao AP5
            else:
                sta_x, sta_y = 60, 60  # Próximo ao AP6

            sta = net.addStation(
                host.name,
                mac=host.mac,
                ip=host.ip,
                position=f'{sta_x},{sta_y},0',
                range=20,  # Aumentado para melhorar conectividade
                txpower=15  # Potência de transmissão ajustada
            )
            f.write(f"{host.name} {host.mac} {host.ip}\n")
            hosts_array.append(sta)

    # Ajusta o modelo de propagação
    net.setPropagationModel(model="logDistance", exp=3)  # Reduzido para simular ambiente menos atenuado

    info("*** Configurando nós WiFi\n")
    net.configureWifiNodes()

    info("*** Criando links\n")
    net.addLink(ap1, ap2, cls=TCLink)
    net.addLink(ap2, ap3, cls=TCLink)
    net.addLink(ap3, ap4, cls=TCLink)
    net.addLink(ap4, ap5, cls=TCLink)
    net.addLink(ap5, ap6, cls=TCLink)

    net.addLink(server, ap1, cls=TCLink)
    net.addLink(server, ap2, cls=TCLink)
    net.addLink(server, ap3, cls=TCLink)
    net.addLink(server, ap4, cls=TCLink)
    net.addLink(server, ap5, cls=TCLink)
    net.addLink(server, ap6, cls=TCLink)

    net.plotGraph(min_x=0, max_x=100, min_y=0, max_y=100)

    info("*** Iniciando a rede\n")
    net.build()
    c1.start()
    ap1.start([c1])
    ap2.start([c1])
    ap3.start([c1])
    ap4.start([c1])
    ap5.start([c1])
    ap6.start([c1])

    info("*** Executando CLI\n")
    CLI(net)

    info("*** Parando a rede\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()