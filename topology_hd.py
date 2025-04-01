import sys

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController
from mn_wifi.node import OVSKernelAP
from mn_wifi.link import wmediumd
from mininet.link import TCLink
from mn_wifi.wmediumdConnector import interference

N_hosts = 15

mappings_file_path = "mappings.txt"

class Host:
    def __init__(self, name, mac, ip):
        self.name = name
        self.mac = mac
        self.ip = ip

hostsInfo = []
hostsArray = []

for i in range(N_hosts):
    Nsta = i + 1
    NIP = i + 2
    Nmac = i + 2
    CurrentHost = Host('sta' + str(Nsta),
                       '00:00:00:00:00:' + format(Nmac, '02x'),
                       '10.0.0.' + str(NIP) + '/8')
    hostsInfo.append(CurrentHost)

def topology():
    info("*** Creating network\n")
    net = Mininet_wifi(controller=RemoteController,
                       accessPoint=OVSKernelAP,
                       autoAssociation=False,
                       link=wmediumd, wmediumd_mode=interference)

    info("*** Adding 6 APs and controllers\n")

    ap1 = net.addAccessPoint('ap1', ssid='ssid-ap1', channel='1', mode='g', position='20,20,0', range=30, txpower=22)
    ap2 = net.addAccessPoint('ap2', ssid='ssid-ap2', channel='6', mode='g', position='40,20,0', range=30, txpower=22)
    ap3 = net.addAccessPoint('ap3', ssid='ssid-ap3', channel='11', mode='g', position='60,20,0', range=30, txpower=22)
    ap4 = net.addAccessPoint('ap4', ssid='ssid-ap4', channel='1', mode='g', position='20,40,0', range=30, txpower=22)
    ap5 = net.addAccessPoint('ap5', ssid='ssid-ap5', channel='6', mode='g', position='40,40,0', range=30, txpower=22)
    ap6 = net.addAccessPoint('ap6', ssid='ssid-ap6', channel='11', mode='g', position='60,40,0', range=30, txpower=22)

    c1 = net.addController('c1', controller=RemoteController)

    info("*** Adding stations to the topology\n")

    server = net.addHost('server', mac='00:00:00:00:00:01', ip='10.0.0.1/8')

    staPositions = [
        '15,15,0', '25,15,0', '35,15,0', '45,15,0', '55,15,0',  # AP1/AP2/AP3
        '15,35,0', '25,35,0', '35,35,0', '45,35,0', '55,35,0',  # AP4/AP5/AP6
        '20,25,0', '30,25,0', '40,25,0', '50,25,0', '60,25,0'   # Mixed
    ]

    f = open(mappings_file_path, "w")
    for i in range(N_hosts):
        sta = net.addStation(hostsInfo[i].name,
                             mac=hostsInfo[i].mac, ip=hostsInfo[i].ip,
                             position=staPositions[i % len(staPositions)], range=13)
        f.write(hostsInfo[i].name + " " + hostsInfo[i].mac + " " + hostsInfo[i].ip + "\n")
        hostsArray.append(sta)

    f.close()

    net.setPropagationModel(model="logDistance", exp=5.5)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Creating links\n")
    net.addLink(ap1, ap2)
    net.addLink(ap2, ap3)
    net.addLink(ap4, ap5)
    net.addLink(ap5, ap6)
    net.addLink(ap1, ap4)
    net.addLink(ap2, ap5)
    net.addLink(ap3, ap6)

    net.addLink(server, ap1, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap2, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap3, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap4, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap5, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap6, cls=TCLink, bw=20, r2q=1)

    # Distribute hosts among APs
    for i in range(3):
        net.addLink(hostsArray[i], ap1)
    for i in range(3, 6):
        net.addLink(hostsArray[i], ap2)
    for i in range(6, 9):
        net.addLink(hostsArray[i], ap3)
    for i in range(9, 12):
        net.addLink(hostsArray[i], ap4)
    for i in range(12, 15):
        net.addLink(hostsArray[i], ap5)

    net.plotGraph(min_x=0, max_x=80, min_y=0, max_y=60)

    info("*** Starting network\n")
    net.build()
    c1.start()
    ap1.start([c1])
    ap2.start([c1])
    ap3.start([c1])
    ap4.start([c1])
    ap5.start([c1])
    ap6.start([c1])

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()