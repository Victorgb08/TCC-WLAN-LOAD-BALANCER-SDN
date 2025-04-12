# Balanceador de carga com RYU e Mininet-Wifi

Projeto desenvolvido para o Trabalho de Conclusão de Curso do aluno Victor Guedes Batista, no semestre de 2025/1.

# Instruções para rodar o projeto
## Atualização padrão
```bash
sudo apt update && sudo apt upgrade -y
```
```bash
sudo apt install git python3-pip -y
```

## Instalar o mininet-wifi
```bash
git clone https://github.com/intrig-unicamp/mininet-wifi.git
cd mininet-wifi
sudo util/install.sh -Wlnfv
cd ..
```
## Clonar o projeto
```bash
git clone https://github.com/Victorgb08/TCC-WLAN-LOAD-BALANCING-SDN
```
## Criar ambiente com versão correta do python e dependências
```bash
sudo apt install -y git python3 python3-pip python3-venv \
                   python3-setuptools python3-dev \
                   net-tools curl unzip
```
```bash
sudo apt update && sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev -y
sudo apt install redis-server -y
sudo apt install iperf3 -y
```
```bash
cd TCC-WLAN-LOAD-BALANCING-SDN
python3.9 -m venv ryu-env
source ryu-env/bin/activate
pip install ryu eventlet==0.30.2
pip install redis
ryu-manager --version
```

## Rodar o projeto base
### Termninal 1
```bash
deactivate
sudo python3 topology.py
```
### Terminal 2
```bash
source ryu-env/bin/activate
sudo ryu-manager app.py
```
### Terminal 3
```bash
sudo chmod +x generate_traffic.sh
sudo chmod +x m
sudo ./generate_traffic.sh
```