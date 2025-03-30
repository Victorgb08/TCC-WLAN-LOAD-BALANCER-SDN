# Balanceador de carga com RYU e Mininet-Wifi

Projeto desenvolvido para o Trabalho de Conclusão de Curso do aluno Victor Guedes Batista, no semestre de 2025/1.

# Instruções para rodar o projeto
## Atualização padrão
sudo apt update && sudo apt upgrade -y


## Instalar o mininet-wifi
git clone https://github.com/intrig-unicamp/mininet-wifi.git
cd mininet-wifi
sudo util/install.sh -Wlnfv
cd ..

## Clonar o projeto
git clone https://github.com/Victorgb08/TCC-WLAN-LOAD-BALANCING-SDN

## Criar ambiente com versão correta do python
sudo apt install -y git python3 python3-pip python3-venv \
                   python3-setuptools python3-dev \
                   net-tools curl unzip
cd TCC-WLAN-LOAD-BALANCING-SDN
python3.9 -m venv ryu-env
source ryu-env/bin/activate
pip install ryu eventlet==0.30.2

ryu-manager --version

## Rodar o projeto base
### Termninal 1
deactivate
python3 topology.py

### Terminal 2
source ryu-env/bin/activate
ryu-manager app.py

### Terminal 3
sudo chmod +x generate_traffic.sh
sudo chmod +x m
sudo ./generate_traffic.sh