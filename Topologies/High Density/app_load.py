from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib import hub

import redis
import pickle

LOAD_THRESHOLD = 22  # 32 Mbps
SIGNAL_THRESHOLD = -95  # dBm

mappings_path = "mappings.txt"

station_name_mappings = {}
name_ip_mac_mappings = {}

def read_mappings():
    with open(mappings_path) as f:
        for line in f:
            data = line.split(' ')
            station_name_mappings[data[1]] = data[0]
            name_ip_mac_mappings[data[0]] = {
                "ip": data[2].split('/')[0],
                "mac": data[1]
            }

    print('mapping', name_ip_mac_mappings)

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        read_mappings()
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.statistics = []
        self.datapaths = {}

        # Redis setup
        self.redis = redis.Redis('127.0.0.1')
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(['statistics'])
        self.monitor_thread = hub.spawn(self.monitor)

    def monitor(self):
        self.logger.info("Iniciando thread de monitoramento de APs.")
        for item in self.pubsub.listen():
            tmp = item['data']
            # Ignore the first/initial return
            if tmp == 1:
                continue
            self.statistics = pickle.loads(tmp)
    
            print("\n=========================== Estatísticas Recebidas ===========================")
            for ap_stat in self.statistics:
                print(f"AP: {ap_stat['name']} (SSID: {ap_stat['ssid']})")
                print(f"  Total de Estações Associadas: {len(ap_stat['stations_associated'])}")
                print(f"  Taxa Total de Recepção (RX): {ap_stat.get('total_rx_rate', 0):.2f} Mbps")
                print(f"  Taxa Total de Transmissão (TX): {ap_stat.get('total_tx_rate', 0):.2f} Mbps")
                for station, station_info in ap_stat['stations_associated'].items():
                    print(f"    Estação: {station}")
                    print(f"      Sinal dos APs Disponíveis: {station_info.get('aps', {})}")
                    print(f"      Taxa de Recepção (RX): {station_info.get('rx_rate', 0):.2f} Mbps")
                    print(f"      Taxa de Transmissão (TX): {station_info.get('tx_rate', 0):.2f} Mbps")
                print("-------------------------------------------------------------------------------")
            print("===============================================================================")
    
            oaps = self.get_overloaded_aps()
            print("\n=========================== APs Sobrecarregados ===========================")
            for ap in oaps:
                print(f"AP: {ap['name']} (Conexões: {len(ap['stations_associated'])}")
                print(f"  Taxa Total de Recepção (RX): {ap.get('total_rx_rate', 0):.2f} Mbps")
                print(f"  Taxa Total de Transmissão (TX): {ap.get('total_tx_rate', 0):.2f} Mbps")
            print("===============================================================================")
    
            uaps = self.get_underloaded_aps()
            print("\n=========================== APs Subutilizados ===========================")
            for ap in uaps:
                print(f"AP: {ap['name']} (Conexões: {len(ap['stations_associated'])}")
                print(f"  Taxa Total de Recepção (RX): {ap.get('total_rx_rate', 0):.2f} Mbps")
                print(f"  Taxa Total de Transmissão (TX): {ap.get('total_tx_rate', 0):.2f} Mbps")
            print("===============================================================================")
    
            if oaps and len(oaps) > 0 and uaps and len(uaps) > 0:
                station, new_ap = self.get_possible_handover(oaps, uaps)
    
                if station and new_ap:
                    print("\n=========================== Migração Planejada ===========================")
                    print(f"Estação a ser migrada: {station}")
                    print(f"Novo AP: {new_ap}")
                    print("===============================================================================")
    
                    migration_instruction = {'station_name': station, 'ssid': new_ap}
                    pvalue = pickle.dumps(migration_instruction)
                    self.delete_flows_with_ip_and_mac(name_ip_mac_mappings[station])
                    self.redis.publish("sdn", pvalue)

    def get_overloaded_aps(self):
        overloaded_aps = []
        for stat in self.statistics:
            total_rx_rate = 0
            total_tx_rate = 0
            for station in stat['stations_associated']:
                total_rx_rate += stat['stations_associated'][station].get('rx_rate', 0)
                total_tx_rate += stat['stations_associated'][station].get('tx_rate', 0)
            if total_rx_rate > LOAD_THRESHOLD or total_tx_rate > LOAD_THRESHOLD:
                stat['total_rx_rate'] = total_rx_rate
                stat['total_tx_rate'] = total_tx_rate
                overloaded_aps.append(stat)

        return overloaded_aps

    def get_underloaded_aps(self):
        underloaded_aps = []
        for stat in self.statistics:
            total_rx_rate = 0
            total_tx_rate = 0
            for station in stat['stations_associated']:
                total_rx_rate += stat['stations_associated'][station].get('rx_rate', 0)
                total_tx_rate += stat['stations_associated'][station].get('tx_rate', 0)
            if total_rx_rate < LOAD_THRESHOLD and total_tx_rate < LOAD_THRESHOLD:
                stat['total_rx_rate'] = total_rx_rate
                stat['total_tx_rate'] = total_tx_rate
                underloaded_aps.append(stat)

        return underloaded_aps

    def get_possible_handover(self, oaps, uaps):
        for oap in oaps:
            print(f"\nAnalisando AP sobrecarregado: {oap['name']} (Total RX: {oap['total_rx_rate']}, Total TX: {oap['total_tx_rate']})")
            for station in oap['stations_associated']:
                station_aps = oap['stations_associated'][station].get('aps', {})
                station_rx = oap['stations_associated'][station].get('rx_rate', 0)
                station_tx = oap['stations_associated'][station].get('tx_rate', 0)
    
                print(f"  Estação: {station} (RX: {station_rx}, TX: {station_tx})")
    
                # Exibir o sinal entre a estação e os APs conhecidos
                if station_aps:
                    print(f"    Sinais entre {station} e APs:")
                    for ap, signal in station_aps.items():
                        print(f"      AP: {ap}, Sinal: {signal} dBm")
                else:
                    print(f"    Nenhuma informação de sinal disponível para a estação {station}.")
    
                # Verificar APs subutilizados que podem receber a estação
                uap_available_ssids = set()
                for ap in uaps:
                    new_rx_rate = ap['total_rx_rate'] + station_rx
                    new_tx_rate = ap['total_tx_rate'] + station_tx
                    if new_rx_rate < LOAD_THRESHOLD and new_tx_rate < LOAD_THRESHOLD:
                        uap_available_ssids.add(ap['ssid'])
                        print(f"    AP subutilizado: {ap['name']} (Total RX: {ap['total_rx_rate']}, Total TX: {ap['total_tx_rate']})")
                        print(f"      Após migração: RX: {new_rx_rate}, TX: {new_tx_rate} (Dentro do limite: {LOAD_THRESHOLD})")
                    else:
                        print(f"    AP subutilizado: {ap['name']} (Total RX: {ap['total_rx_rate']}, Total TX: {ap['total_tx_rate']})")
                        print(f"      Após migração: RX: {new_rx_rate}, TX: {new_tx_rate} (Excede o limite: {LOAD_THRESHOLD})")
    
                # Verificar se o sinal é forte o suficiente no novo AP
                strong_ssids = set(
                    [ap for ap in station_aps if float(station_aps[ap]) > SIGNAL_THRESHOLD and ap != oap['ssid']]
                )
                if not strong_ssids:
                    print(f"    Nenhum AP com sinal forte suficiente para a estação {station} (Sinal mínimo: {SIGNAL_THRESHOLD} dBm)")
                else:
                    print(f"    APs com sinal forte para a estação {station}: {strong_ssids}")
    
                # Encontrar interseção entre APs disponíveis e com sinal forte
                possible_uaps = strong_ssids & uap_available_ssids
                if len(possible_uaps) > 0:
                    new_ap = next(iter(possible_uaps))
                    print(f"  Handover possível: Estação {station} -> Novo AP: {new_ap}")
                    return station, new_ap
                else:
                    print(f"  Handover não possível para a estação {station}:")
                    if not uap_available_ssids:
                        print("    - Nenhum AP subutilizado disponível.")
                    if not strong_ssids:
                        print("    - Nenhum AP com sinal forte suficiente.")
                    if uap_available_ssids and strong_ssids:
                        print("    - Nenhum AP atende ambas as condições (capacidade e sinal).")
    
        return None, None

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.datapaths[datapath.id] = datapath
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    idle_timeout=idle,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority, idle_timeout=idle,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def delete_flows_with_ip_and_mac(self, ip_and_mac):
        ip = ip_and_mac['ip']
        mac = ip_and_mac['mac']
        for dp in self.datapaths.values():
            # IP as destination
            parser = dp.ofproto_parser
            match = parser.OFPMatch(ipv4_dst=ip, eth_type=0x0800)
            mod = parser.OFPFlowMod(datapath=dp,
                                    command=dp.ofproto.OFPFC_DELETE,
                                    out_port=dp.ofproto.OFPP_ANY, out_group=dp.ofproto.OFPG_ANY,
                                    priority=1, match=match)
            print(f'Deleting flows with IP {ip} as destination')
            dp.send_msg(mod)

            # IP as source
            match = parser.OFPMatch(ipv4_src=ip, eth_type=0x0800)
            mod = parser.OFPFlowMod(datapath=dp,
                                    command=dp.ofproto.OFPFC_DELETE,
                                    out_port=dp.ofproto.OFPP_ANY, out_group=dp.ofproto.OFPG_ANY,
                                    priority=1, match=match)
            dp.send_msg(mod)
            print(f'Deleting flows with IP {ip} as source')

            # MAC as destination
            match = parser.OFPMatch(eth_dst=mac)
            mod = parser.OFPFlowMod(datapath=dp,
                                    command=dp.ofproto.OFPFC_DELETE,
                                    out_port=dp.ofproto.OFPP_ANY, out_group=dp.ofproto.OFPG_ANY,
                                    priority=1, match=match)

            dp.send_msg(mod)
            print(f'Deleting flows with MAC {mac} as destination')

            # MAC as source
            match = parser.OFPMatch(eth_src=mac)
            mod = parser.OFPFlowMod(datapath=dp,
                                    command=dp.ofproto.OFPFC_DELETE,
                                    out_port=dp.ofproto.OFPP_ANY, out_group=dp.ofproto.OFPG_ANY,
                                    priority=1, match=match)
            dp.send_msg(mod)
            print(f'Deleting flows with MAC {mac} as source')

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("Packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # Ignore LLDP packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            if eth.ethertype == ether_types.ETH_TYPE_IP:
                ip = pkt.get_protocol(ipv4.ipv4)
                srcip = ip.src
                dstip = ip.dst
                match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                        ipv4_src=srcip,
                                        ipv4_dst=dstip)
                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    self.add_flow(datapath, 1, match, actions, msg.buffer_id, idle=30)
                    return
                else:
                    self.add_flow(datapath, 1, match, actions, idle=30)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)