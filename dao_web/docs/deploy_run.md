
# 部署文档


### 0x00. Centos 7 初始化

配置网络 static IP
```bash
vi /etc/sysconfig/network-scripts/ifcfg-eth0

BOOTPROTO=static
IPADDR=192.168.9.119
NETMASK=255.255.255.0
GATEWAY=192.168.9.1
DNS1=223.5.5.5
DNS2=123.125.81.6
ONBOOT=yes
```
安装必要软件
```bash
yum -y install epel-release zip unzip bzip2 wget git vim redis gcc make screen
```

更新证书
```
yum -y update ca-certificates
```

安装 k-vim
```bash
cd /opt
git clone https://github.com/wklken/vim-for-server.git
cp vimrc ~/.vimrc
```

关闭 SELinux
```
vim /etc/selinux/config
SELINUX="disabled"
```

安装 Iptables
```
yum -y install iptables-services
vim /etc/sysconfig/iptables
systemctl start iptables && systemctl enable iptables
```

安装 Anaconda3
```
wget https://repo.anaconda.com/archive/Anaconda3-2019.03-Linux-x86_64.sh
sh Anaconda3-2019.03-Linux-x86_64.sh
```

### 0x01. 配置 redis
```bash
vim /etc/redis.conf
bind 0.0.0.0
port 6379
requirepass foobared
systemctl start redis && systemctl enable redis
```

### 0x02. 安装 Ta-Lib
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

# import talib
# import numpy as np
# l = [1.2,3.1,3,5,6,7,8]
# a = np.array(l)
# talib.SMA(a, 2)
import talib;import numpy as np;talib.SMA(np.array([1.2,3.1,3,5,6,7,8]), 2)
```

### 0x03. 安装 MongoDB (CentOS 7)

安装的版本为 MongoDB 4.4
```bash
vi /etc/yum.repos.d/mongodb-org-4.4.repo

[mongodb-org-4.4]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/4.4/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.4.asc

# yum install mongodb-org -y

systemctl start mongod.service
systemctl enable mongod.service
```
处理报错  #rm /tmp/mongodb-32018.sock

#### 0x03-1. 单节点模式

```bash
# mongo -p 27017
> use admin
> db.createUser({user: "username",pwd: "password", roles: ["root"]})
> db.auth('username', 'password')

> use dao_trade;
> db.createUser({user: 'user_name', pwd: 'passwd', roles: [{role: "readWrite", db: "dao_trade"}]});
```
数据备份与恢复
```bash
# mongodump -h 127.0.0.1 -p 27017 --username=username --password=password -d dao_trade -o ./
# mongodump --host=127.0.0.1:37017 --username=username --password=password -d dao_trade -o ./

# mongorestore -h 127.0.0.1 -p 27017 --username=username --password=pass -d dao_trade --dir dao_trade/
```

#### 0x03-2. ReplicaSet 模式

写配置文件
```bash
# vim /etc/mongod1.conf
# mongod.conf

# for documentation of all options, see:
#   http://docs.mongodb.org/manual/reference/configuration-options/

# where to write logging data.
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb1/mongod.log

# Where and how to store data.
storage:
  dbPath: /var/lib/mongo1
  journal:
    enabled: true
#  engine:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1
      directoryForIndexes: true

# how the process runs
processManagement:
  fork: true  # fork and run in background
  pidFilePath: /var/run/mongodb1/mongod.pid  # location of pidfile
  timeZoneInfo: /usr/share/zoneinfo

# network interfaces
net:
  port: 37011
  bindIp: 0.0.0.0  # Enter 0.0.0.0,:: to bind to all IPv4 and IPv6 addresses or, alternatively, use the net.bindIpAll setting.

security:
  keyFile: /var/lib/mongo1/keyfile
  authorization: "enabled"

#operationProfiling:

replication:
  replSetName: dao

#sharding:

## Enterprise-Only Options

#auditLog:

#snmp:

```
部署运行起来
```bash
# mkdir -p /var/log/mongodb1
# mkdir -p /var/log/mongodb2
# mkdir -p /var/log/mongodb3
# mkdir -p /var/lib/mongo1
# mkdir -p /var/lib/mongo2
# mkdir -p /var/lib/mongo3
# mkdir -p /var/run/mongodb1 && mkdir -p /var/run/mongodb2 && mkdir -p /var/run/mongodb3

# /usr/bin/mongod -f /etc/mongod1.conf
# /usr/bin/mongod -f /etc/mongod2.conf
# /usr/bin/mongod -f /etc/mongod3.conf

# openssl rand -base64 90 > keyfile
# chmod 600 keyfile

# mongorestore -h "mongos/192.168.99.105:17017,192.168.99.105:17018,192.168.99.105:17019" --username=username --password='pwd' -d dao_trade --drop --dir dao_trade/
# mongodump -h 'mongors/192.168.100.1:27017,192.168.100.2:27017' -u 'username' -p 'pwd' --oplog --authenticationDatabase admin --gzip -o ${备份目录绝对路径}
# mongors是副本集的名字，为了从主节点进行备份
# 需要先创建 dao_trade 数据库，再进行数据恢复

# mongo --port 37011
> use admin;
> db.createUser({user: "username",pwd: "password", roles: ["root"]})
> db.auth('username', 'password')
> rs.initiate();
> rs.reconfig({_id: "dao",members: [{ _id : 0, host : "192.168.9.105:37011" },{ _id : 1, host : "192.168.9.105:37012" },{ _id : 2, host : "192.168.9.105:37013" }]});
> rs.status();
> cfg = rs.conf()
> cfg.members[0].priority = 2
> cfg.members[1].priority = 1
> cfg.members[2].priority = 0.5
> rs.reconfig(cfg)
> # rs.add("192.168.99.105:37013")

# mongo --port 37011 -u username -p password
> use dao_trade;
> db.createUser({user: 'user_name', pwd: 'passwd', roles: [{role: "readWrite", db: "dao_trade"}]});
> use dao_strategy;
> db.createUser({user: 'user_name', pwd: 'passwd', roles: [{role: "readWrite", db: "dao_strategy"}]});
# 调整IP
> rs.reconfig({_id: "dao",members: [{ _id : 0, host : "194.233.83.209:57017" },{ _id : 1, host : "185.106.176.65:57017" },{ _id : 2, host : "194.233.86.220:57017" }]}, {force:true});
# 关闭副本集
> use admin;
> db.shutdownServer();
```

### 0x04. 启动运行

启动 mongod
* `/usr/bin/mongod -f /etc/mongod1.conf`
* `/usr/bin/mongod -f /etc/mongod2.conf`
* `/usr/bin/mongod -f /etc/mongod3.conf`

启动 dao_quote

* `cd /var/www/dao_quote/`
* `screen -dmS dqwss python main.py -t wss`
* `screen -dmS dqg python main.py -t g`
* `screen -dmS dqctp python main.py -t ctp`
* `screen -dmS dqesunny python main.py -t esunny`
* `screen -dmS dqc python main.py -t c`
* `screen -dmS dqr python main.py -t r`
* `screen -dmS dqt python main.py -t t`
* `screen -dmS dqzip python main.py -t zip`
* `screen -dmS dqrpc python main.py -t rpc`
* `uwsgi --ini dq_uwsgi.ini`

启动 dao_web
* `cd /var/www/dao_web/`
* `screen -S dww`
* `python manage.py -t runserver`

启动 dao_user
* `cd /var/www/dao_user`
* `screen -S dur`
* `python manage.py -t rpc`

启动 dao_execute
* `cd /var/www/dao_execute`
* `screen -S der`
* `python manage.py -t rpc`
* `screen -S mctp`
*  `python manage.py -t mctp`
*  `screen -S update_orders`
*  `python manage.py -t orders`

启动 dao_strategy
* `cd /var/www/dao_strategy`
* `screen -S dsr`
* `python manage.py -t rpc`
* `screen -S dssend`
* `python manage.py -t send`
* `screen -S dspush`
* `python manage.py -t push`
* `screen -S dsd`
* `python manage.py -t backd -n 9`
* `screen -S dsmon`
* `python manage.py -t monitor`
* `screen -S fresh_primary`
* `python manage.py -t fresh_primary`
* `screen -S dss`
* `cd dao_strategy/live`
* `python manage_strategy.py -t real -s yes`

关闭策略
* `ps auxww | grep 'python manage_strategy.py -t real -s yes -n' | awk '{print $2}' | xargs kill -9`