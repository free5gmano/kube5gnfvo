# 安裝必要工具
sudo apt-get update
sudo apt-get install -y git make gcc

cd ~
git clone https://github.com/free5gc/gtp5g.git
cd gtp5g

# ⭐ 這行是關鍵（鎖版本）
git checkout v0.9.5

# 編譯與安裝
make clean
make
sudo make install

# 載入 module
sudo modprobe gtp5g

# 驗證
lsmod | grep -i gtp
modinfo gtp5g | grep version