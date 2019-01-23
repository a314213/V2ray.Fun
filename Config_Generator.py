#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import urllib2
import commands

def getip():
    myip = urllib2.urlopen('https://cn.fdos.me/ip.php').read()
    myip = myip.strip()
    return str(myip)

def open_port(port):
    cmd =[ "iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport $1 -j ACCEPT",
            "iptables -I INPUT -m state --state NEW -m udp -p udp --dport $1 -j ACCEPT",
            "ip6tables -I INPUT -m state --state NEW -m tcp -p tcp --dport $1 -j ACCEPT",
            "ip6tables -I INPUT -m state --state NEW -m udp -p udp --dport $1 -j ACCEPT"]

    for x in cmd:
        x = x.replace("$1",str(port))
        commands.getoutput(x)

def gen_server():

    data_file = open("/usr/local/V2ray.Fun/v2ray.config", "r")
    data = json.loads(data_file.read())
    data_file.close()

    server_websocket = json.loads("""
    {
  "path": "/apiTest",
  "headers": {
    "Host": ""
  }
}
    """)

    server_mkcp = json.loads("""
    {
        "uplinkCapacity": 20,
        "downlinkCapacity": 100,
        "readBufferSize": 2,
        "mtu": 1350,
        "header": {
          "request": null,
          "type": "none",
          "response": null
        },
        "tti": 50,
        "congestion": false,
        "writeBufferSize": 2
      }
    """)

    server_tls = json.loads("""
    {
                "certificates": [
                    {
                        "certificateFile": "/path/to/example.domain/fullchain.cer",
                        "keyFile": "/path/to/example.domain.key"
                    }
                ]
            }
    """)

    server_raw = """
{
    "log": {
      "access": "/var/log/v2ray/access.log",
      "loglevel": "warning",
      "error": "/var/log/v2ray/error.log"
    },
    "stats": {},
    "outbounds": [
      {
        "settings": {},
        "protocol": "freedom"
      },
      {
        "settings": {},
        "protocol": "blackhole",
        "tag": "blocked"
      }
    ],
    "api": {
      "services": [
        "StatsService"
      ],
      "tag": "api"
    },
    "policy": {
      "system": {
        "statsInboundUplink": true,
        "statsInboundDownlink": true
      },
      "levels": {
        "0": {
          "statsUserDownlink": true,
          "statsUserUplink": true
        },
        "1": {
            "statsUserDownlink": true,
            "statsUserUplink": true
        }
      }
    },
    "routing": {
        "strategy": "rules",
        "rules": [
            {
            "outboundTag": "blocked",
            "type": "field",
            "ip": [
                "0.0.0.0/8",
                "10.0.0.0/8",
                "100.64.0.0/10",
                "169.254.0.0/16",
                "172.16.0.0/12",
                "192.0.0.0/24",
                "192.0.2.0/24",
                "192.168.0.0/16",
                "198.18.0.0/15",
                "198.51.100.0/24",
                "203.0.113.0/24",
                "::1/128",
                "fc00::/7",
                "fe80::/10"
            ]
            },
            {
            "outboundTag": "api",
            "type": "field",
            "inboundTag": [
                "api"
            ]
            }
        ]
    },
    "inbounds": [
      {
        "settings": {
          "clients": [
            {
                "id": "",
                "email": "a@mail",
                "level": 0,
                "alterId": 39
            }
          ]
        },
        "tag": "main",
        "protocol": "vmess",
        "port": 8079,
        "listen": "127.0.0.1",
        "streamSettings": {
          "tcpSettings": {},
          "kcpSettings": {
          },
          "quicSettings": {},
          "httpSettings": {},
          "security": "auto",
          "network": "ws",
          "wsSettings": {}
          },
          "tlsSettings": {}
      },
      {
        "settings": {
          "address": "127.0.0.1"
        },
        "protocol": "dokodemo-door",
        "tag": "api",
        "listen": "127.0.0.1",
        "port": 62105
      }
    ]
  }
    """
    server = json.loads(server_raw)
    if data['protocol'] == "vmess":
        server['inbounds'][0]['port'] = int(data['port'])
        server['inbounds'][0]['settings']['clients'][0]['id'] = data['uuid']
        #server['inbounds'][0]['settings']['clients'][0]['security'] = data['encrypt']

    elif data['protocol'] == "mtproto":
        """ MTProto don't needs client config, just use Telegram"""
        server['inbounds'][0]['port'] = int(data['port'])
        server['inbounds'][0]['protocol'] = "mtproto"   
        server['inbounds'][0]['settings'] = dict()
        server['inbounds'][0]['settings']['users'] = list()
        server['inbounds'][0]['settings']['users'].append({'secret': data['secret']})
        server['inbounds'][0]['tag'] = "tg-in"

        server['inbounds'][0]['protocol'] = "mtproto"
        server['inbounds'][0]['tag'] = "tg-out"


        server['routing']['settings']['rules'].append({
            "type": "field",
            "inboundTag": ["tg-in"],
            "outboundTag": "tg-out"})

    if data['trans'] == "tcp":
        server['inbounds'][0]['streamSettings']=dict()
        server['inbounds'][0]['streamSettings']['network'] = "tcp"

    elif data['trans'].startswith("mkcp"):
        server['inbounds'][0]['streamSettings'] = dict()
        server['inbounds'][0]['streamSettings']['network'] = "kcp"
        server['inbounds'][0]['streamSettings']['kcpSettings'] = server_mkcp

        if data['trans'] == "mkcp-srtp":
            server['inbounds'][0]['streamSettings']['kcpSettings']['header']['type'] = "srtp"
        elif data['trans'] == "mkcp-utp":
            server['inbounds'][0]['streamSettings']['kcpSettings']['header']['type'] = "utp"
        elif data['trans'] == "mkcp-wechat":
            server['inbounds'][0]['streamSettings']['kcpSettings']['header']['type'] = "wechat-video"

    elif data['trans'] == "websocket":
        server['inbounds'][0]['streamSettings'] = dict()
        server['inbounds'][0]['streamSettings']['network'] = "ws"
        server['inbounds'][0]['streamSettings']['wsSettings'] = server_websocket
        server['inbounds'][0]['streamSettings']['wsSettings']['path'] = "/" + data['path']
        server['inbounds'][0]['streamSettings']['wsSettings']['headers']['Host'] = data['domain']

    if data['tls'] == "on":
        if data['nginx'] != "on":
            server['inbounds'][0]['streamSettings']['security'] = "tls"
            server_tls['certificates'][0]['certificateFile'] = "/root/.acme.sh/{0}/fullchain.cer".format(data['domain'])
            server_tls['certificates'][0]['keyFile'] = "/root/.acme.sh/{0}/{0}.key".format(data['domain'],data['domain'])
            server['inbounds'][0]['streamSettings']['tlsSettings'] = server_tls

    server_file = open("/etc/v2ray/config.json","w")
    server_file.write(json.dumps(server,indent=2))
    server_file.close()


def gen_client():
    client_raw = """
   {
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
  {
    "port": 1088,
    "listen": "0.0.0.0",
    "protocol": "http",
    "settings": {
      "auth": "noauth",
      "udp": true
    },
    "streamSettings": {
      "sockopt": {
        "mark": 255
      }
    }
  },
  {
    "port": 1099,
    "listen": "0.0.0.0",
    "protocol": "dokodemo-door",
    "settings": {
      "network": "tcp,udp",
      "timeout": 360,
      "followRedirect": true
    }
  },
  {
    "port": 1100,
    "listen": "0.0.0.0",
    "protocol": "dokodemo-door",
    "settings": {
      "address": "8.8.8.8",
      "port": 53,
      "network": "udp",
      "timeout": 30,
      "followRedirect": false
    }
  }
  ],
  "outbounds": [
    {
      "protocol": "vmess",
      "tag": "detour",
      "settings": {
        "vnext": [
          {
            "address": "",
            "port": 0,
            "users": [
              {
                  "id": "",
                  "alterId": 39
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "sockopt": {
          "mark": 255
        },
        "security": "auto",
        "network": "ws",
        "wsSettings": {
          "path": ""
        }
      },
      "mux": {
        "enabled": true
      } 
    },
    {
      "protocol": "freedom",
      "settings": {},
      "tag": "direct",
      "streamSettings": {
        "sockopt": {
          "mark": 255
        }
      }
    }
  ],
  "dns": {
    "servers": [
      "8.8.8.8",
      "8.8.4.4",
      "localhost"
    ]
  },
  "routing": {    
    "domainStrategy": "IPIfNonMatch", 
    "rules": [
      {
        "domain":[
          "amazon.com",
          "microsoft.com",
          "jd.com",
          "youku.com",
          "baidu.com",
          "taobao.com",
          "tmall.com",
          "geosite:cn"
        ],
        "type": "field",
        "outboundTag": "direct"
      },
      {
        "type": "field",
        "ip": [
          "0.0.0.0/8",
          "10.0.0.0/8",
          "100.64.0.0/10",
          "169.254.0.0/16",
          "172.16.0.0/12",
          "192.0.0.0/24",
          "192.0.2.0/24",
          "192.168.0.0/16",
          "198.18.0.0/15",
          "198.51.100.0/24",
          "203.0.113.0/24",
          "188.188.188.188/32",
          "110.110.110.110/32",
          "::1/128",
          "fc00::/7",
          "fe80::/10"
        ],
        "outboundTag": "direct"
      },
      {
        "type": "chinasites",
        "outboundTag": "direct"
      },
      {
        "type": "chinaip",
        "outboundTag": "direct"
      }
      
    ]
  }
}
    """
    cLient_mkcp = json.loads("""
    {
                "mtu": 1350,
                "tti": 50,
                "uplinkCapacity": 20,
                "downlinkCapacity": 100,
                "congestion": false,
                "readBufferSize": 2,
                "writeBufferSize": 2,
                "header": {
                    "type": "none"
                }
    }
    """)
    client = json.loads(client_raw)
    data_file = open("/usr/local/V2ray.Fun/v2ray.config", "r")
    data = json.loads(data_file.read())
    data_file.close()

    if data['mux'] == "on":
        client['outbounds'][0]['mux']['enabled'] = True
    elif data['mux'] == "off":
        client['outbounds'][0]['mux']['enabled'] = False

    if data['domain'] == "none":
        client['outbounds'][0]['settings']['vnext'][0]['address'] = data['ip']
    else:
        client['outbounds'][0]['settings']['vnext'][0]['address'] = data['domain']

    client['outbounds'][0]['settings']['vnext'][0]['port'] = int(data['port'])
    client['outbounds'][0]['settings']['vnext'][0]['users'][0]['id'] = data['uuid']
    client['outbounds'][0]['settings']['vnext'][0]['users'][0]['security'] = data['encrypt']


    if data['trans'] == "websocket":
        client['outbounds'][0]['streamSettings']['network'] = "ws"
        client['outbounds'][0]['streamSettings']['wsSettings']['path'] = "/" + data['path']
        if data['nginx'] == "on":
            if data['tls'] == "on":
                client['outbounds'][0]['settings']['vnext'][0]['port'] = 443
            else:
                client['outbounds'][0]['settings']['vnext'][0]['port'] = 80

    elif data['trans'].startswith("mkcp"):
        if data['trans'] == "mkcp-srtp":
            cLient_mkcp['header']['type'] = "srtp"
        elif data['trans'] == "mkcp-utp":
            cLient_mkcp['header']['type'] = "utp"
        elif data['trans'] == "mkcp-wechat":
            cLient_mkcp['header']['type'] = "wechat-video"

        client['outbounds'][0]['streamSettings']['network'] = "kcp"
        client['outbounds'][0]['streamSettings']['kcpSettings'] = cLient_mkcp

    elif data['trans'] == "tcp":
        client['outbounds'][0]['streamSettings']['network'] = "tcp"


    if data['tls'] == "on":
        client['outbounds'][0]['streamSettings']['security'] = "tls"

    client_file = open("/root/config.json","w")
    client_file.write(json.dumps(client,indent=2))
    client_file.close()

    client_file = open("/usr/local/V2ray.Fun/static/config.json", "w")
    client_file.write(json.dumps(client, indent=2))
    client_file.close()




