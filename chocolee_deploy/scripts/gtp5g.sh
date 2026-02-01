sudo apt-get update
sudo apt-get install -y git make gcc

cd ~
rm -rf gtp5g
git clone https://github.com/free5gc/gtp5g.git
cd gtp5g
make
sudo make install
sudo modprobe gtp5g

# 驗證
lsmod | grep -i gtp
modinfo gtp5g | head