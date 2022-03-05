
# 部署文档


### 0x00. 安装 Ta-Lib
```bash
wget https://nchc.dl.sourceforge.net/project/ta-lib/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz
tar -xvf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
make install
cd /usr
find -name libta_lib.so.0
cp ./src/.libs/libta_lib.so.0 /usr/lib64/
vim /etc/profile line 53
export LD_LIBRARY_PATH=/usr/lib64
# add to bashrc vi ~/.bashrc
# export LD_LIBRARY_PATH="/usr/lib/:$LD_LIBRARY_PATH"
pip install TA-Lib

# test
ipython

import talib
import numpy as np
l = [1.2,3.1,3,5,6,7,8]
a = np.array(l)
talib.SMA(a, 2)
```

### 0x01. Python 依赖

安装 Anaconda
```bash
# wget https://repo.anaconda.com/archive/Anaconda3-2019.03-Linux-x86_64.sh
# sh Anaconda3-2019.03-Linux-x86_64.sh
# vi ~/.bashrc
# LD_LIBRARY_PATH=/root/anaconda3/lib:$LD_LIBRARY_PATH
# export LD_LIBRARY_PATH

```
```bash
# pip install -r requirements.txt -i https://pypi.doubanio.com/simple
# pip install --ignore-installed PyYAML
```

### 0x02. 系统启动

```bash
screen -dmS dsr python manage.py -t rpc && \
screen -dmS send python manage.py -t send && \
screen -dmS push python manage.py -t push && \
screen -dmS backd python manage.py -t backd -n 10 && \
screen -dmS dsmon python manage.py -t monitor &&
```