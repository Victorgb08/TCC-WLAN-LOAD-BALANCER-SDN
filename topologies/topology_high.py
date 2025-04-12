import sys

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController
from mn_wifi.node import OVSKernelAP
from mn_wifi.link import wmediumd
from mininet.link import TCLink
from mn_wifi.wmediumdConnector import interference

N_hosts = 50

mappings_file_path = "mappings/mappings_high.txt"

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

    info("*** Adding 8 APs and controllers\n")

    ap1 = net.addAccessPoint('ap1', ssid='ssid-ap1', channel='1', mode='g', position='10,10,0', range=30, txpower=22)
    ap2 = net.addAccessPoint('ap2', ssid='ssid-ap2', channel='6', mode='g', position='30,10,0', range=30, txpower=22)
    ap3 = net.addAccessPoint('ap3', ssid='ssid-ap3', channel='11', mode='g', position='50,10,0', range=30, txpower=22)
    ap4 = net.addAccessPoint('ap4', ssid='ssid-ap4', channel='1', mode='g', position='70,10,0', range=30, txpower=22)
    ap5 = net.addAccessPoint('ap5', ssid='ssid-ap5', channel='6', mode='g', position='20,30,0', range=30, txpower=22)
    ap6 = net.addAccessPoint('ap6', ssid='ssid-ap6', channel='11', mode='g', position='40,30,0', range=30, txpower=22)
    ap7 = net.addAccessPoint('ap7', ssid='ssid-ap7', channel='1', mode='g', position='60,30,0', range=30, txpower=22)
    ap8 = net.addAccessPoint('ap8', ssid='ssid-ap8', channel='6', mode='g', position='80,30,0', range=30, txpower=22)

    c1 = net.addController('c1', controller=RemoteController)

    info("*** Adding stations to the topology\n")

    server = net.addHost('server', mac='00:00:00:00:00:01', ip='10.0.0.1/8')

    staPositions = [
        '5,5,0', '15,5,0', '25,5,0', '35,5,0', '45,5,0',  # AP1/AP2/AP3/AP4
        '55,5,0', '65,5,0', '75,5,0', '85,5,0', '15,25,0',  # AP5/AP6/AP7/AP8
        '25,25,0', '35,25,0', '45,25,0', '55,25,0', '65,25,0',  # Mixed
        '75,25,0', '85,25,0', '10,20,0', '20,20,0', '30,20,0',  # Mixed
        '40,20,0', '50,20,0', '60,20,0', '70,20,0', '80,20,0',  # Mixed
        '10,30,0', '20,30,0', '30,30,0', '40,30,0', '50,30,0',  # Mixed
        '60,30,0', '70,30,0', '80,30,0', '10,40,0', '20,40,0',  # Mixed
        '30,40,0', '40,40,0', '50,40,0', '60,40,0', '70,40,0',  # Mixed
        '80,40,0', '10,50,0', '20,50,0', '30,50,0', '40,50,0'   # Mixed
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
    net.addLink(ap3, ap4)
    net.addLink(ap5, ap6)
    net.addLink(ap6, ap7)
    net.addLink(ap7, ap8)
    net.addLink(ap1, ap5)
    net.addLink(ap2, ap6)
    net.addLink(ap3, ap7)
    net.addLink(ap4, ap8)

    net.addLink(server, ap1, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap2, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap3, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap4, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap5, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap6, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap7, cls=TCLink, bw=20, r2q=1)
    net.addLink(server, ap8, cls=TCLink, bw=20, r2q=1)

    # Distribute hosts among APs (10 hosts per AP)
    for i in range(10):
        net.addLink(hostsArray[i], ap1)
    for i in range(10, 20):
        net.addLink(hostsArray[i], ap2)
    for i in range(20, 30):
        net.addLink(hostsArray[i], ap3)
    for i in range(30, 40):
        net.addLink(hostsArray[i], ap4)
    for i in range(40, 50):
        net.addLink(hostsArray[i], ap5)

    net.plotGraph(min_x=0, max_x=100, min_y=0, max_y=50)

    info("*** Starting network\n")
    net.build()
    c1.start()
    ap1.start([c1])
    ap2.start([c1])
    ap3.start([c1])
    ap4.start([c1])
    ap5.start([c1])
    ap6.start([c1])
    ap7.start([c1])
    ap8.start([c1])

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()