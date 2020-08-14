#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.node import Host, RemoteController, OVSSwitch
from mininet.link import TCLink
import subprocess


REMOTE_CONTROLLER_IP = "10.0.3.11"

QUAGGA_DIR = '/usr/lib/quagga'
# Must exist and be owned by quagga user (quagga:quagga by default on Ubuntu)
QUAGGA_RUN_DIR = '/var/run/quagga'
CONFIG_DIR = 'configs'

global isp1_h, isp1_s, isp2_h, isp2_s, sdn_h, sdn_s, gwr

class SdnIpHost(Host):
    def __init__(self, name, ip, route, *args, **kwargs):
        Host.__init__(self, name, ip=ip, *args, **kwargs)

        self.name = name
        self.ip = ip
        self.route = route

    def config(self, **kwargs):
        Host.config(self, **kwargs)

        debug("configuring route %s" % self.route)

        self.cmd('ip addr add %s dev %s-eth0' % (self.ip, self.name))
        self.cmd('ip route add default via %s' % self.route)

class Router(Host):
    def __init__(self, name, quaggaConfFile, zebraConfFile, intfDict, *args, **kwargs):
        Host.__init__(self, name, *args, **kwargs)

        self.quaggaConfFile = quaggaConfFile
        self.zebraConfFile = zebraConfFile
        self.intfDict = intfDict

    def config(self, **kwargs):
        Host.config(self, **kwargs)
        self.cmd('sysctl net.ipv4.ip_forward=1')
        self.cmd('sysctl net.ipv6.conf.all.forwarding=1')

        for intf, attrs in self.intfDict.items():
            self.cmd('ip addr flush dev %s' % intf)
            if 'mac' in attrs:
                self.cmd('ip link set %s down' % intf)
                self.cmd('ip link set %s address %s' % (intf, attrs['mac']))
                self.cmd('ip link set %s up ' % intf)
            for addr in attrs['ipAddrs']:
                self.cmd('ip addr add %s dev %s' % (addr, intf))

        self.cmd('/usr/lib/quagga/zebra -d -f %s -z %s/zebra%s.api -i %s/zebra%s.pid' % (self.zebraConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))
        self.cmd('/usr/lib/quagga/bgpd -d -f %s -z %s/zebra%s.api -i %s/bgpd%s.pid' % (self.quaggaConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))


    def terminate(self):
        self.cmd("ps ax | egrep 'bgpd%s.pid|zebra%s.pid' | awk '{print $1}' | xargs kill" % (self.name, self.name))
        Host.terminate(self)

class SdnSwitch(OVSSwitch):
    def __init__(self, name, dpid, *args, **kwargs):
        OVSSwitch.__init__(self, name, dpid=dpid, *args, **kwargs)

    #def start(self, controllers):
    #    OVSSwitch.start(self, controllers)
    #    #self.cmd("ovs-vsctl set bridge %s protocols=OpenFlow13" % self.name)



def createSoDIP6Network( net ):
    global isp_h, isp_s, sdn_h, sdn_s, gwr
    sdn_s,isp_h, sdn_h, gwr = [],[],[],[]
    
    for i in range(1, 6+1):
        sdn_s.append(net.addSwitch('sdn_s%s' % i, dpid='00000000000000a%s' %i))
        
    
    """
    sdn_s1 = net.addSwitch('sdn_s1', dpid='00000000000000a1')
    sdn_s2 = net.addSwitch('sdn_s2', dpid='00000000000000a2')
    sdn_s3 = net.addSwitch('sdn_s3', dpid='00000000000000a3')
    sdn_s4 = net.addSwitch('sdn_s4', dpid='00000000000000a4')
    sdn_s5 = net.addSwitch('sdn_s5', dpid='00000000000000a5')
    sdn_s6 = net.addSwitch('sdn_s6', dpid='00000000000000a6')
    
    sdn_s=[sdn_s1,sdn_s2, sdn_s3, sdn_s4, sdn_s5]
    """
    zebraConf = '%s/zebra.conf' % CONFIG_DIR

    # Switches we want to attach our routers to, in the correct order
    gwrSwitches = [sdn_s[0], sdn_s[1], sdn_s[2], sdn_s[3]]

    for i in range(1, len(gwrSwitches)+1):
        name = 'gwr%s' % i

        eth0 = { 'mac' : '00:00:00:00:0%s:01' % i,
                 'ipAddrs' : ['10.0.%s.1/24' % i, '2001:%s::1' %i ] }
        eth1 = { 'ipAddrs' : ['192.168.%s.254/24' % i, '2001:D192:168:%s::1' % i] }
        intfs = { '%s-eth0' % name : eth0,
                  '%s-eth1' % name : eth1 }

        quaggaConf = '%s/quagga%s.conf' % (CONFIG_DIR, i)

        router = net.addHost(name, cls=Router, quaggaConfFile=quaggaConf,
                              zebraConfFile=zebraConf, intfDict=intfs)
        
        host = net.addHost('isp_h%s' % i, cls=SdnIpHost, 
                            ip='192.168.%s.1/24' % i,
                            route='192.168.%s.254' % i)
        
        isp_h.append(host)
        gwr.append(router)
        
        net.addLink(router, gwrSwitches[i-1])
        net.addLink(router, host)
        host.cmd('ifconfig '+host.name+'-eth0 inet6 add 2001:D192:168:%s::1/64 up' % i)
        host.cmd('route -A inet6 add default gw 2001:D192:168:%s::101' % i)

    # Set up the internal BGP speaker
    bgpEth0 = { 'mac':'00:00:00:00:00:01', 
                'ipAddrs' : ['10.0.1.101/24',
                             '10.0.2.101/24',
                             '10.0.3.101/24',
                             '10.0.4.101/24',
                             '10.0.100.254/24',
                             '2001:1::101/64',
                             '2001:2::101/64',
                             '2001:3::101/64',
                             '2001:4::101/64',
                             '2001:100::254/64',] }
    bgpEth1 = { 'ipAddrs' : ['10.10.10.1/24'] }
    bgpIntfs = { 'bgp-eth0' : bgpEth0,
                 'bgp-eth1' : bgpEth1 }
    
    bgp = net.addHost( "bgp", cls=Router, 
                         quaggaConfFile = '%s/quagga-sdn.conf' % CONFIG_DIR, 
                         zebraConfFile = zebraConf, 
                         intfDict=bgpIntfs )
    
    net.addLink( bgp, sdn_s[4] )

    # Connect BGP speaker to the root namespace so it can peer with ONOS
    root = net.addHost( 'root', inNamespace=False, ip='10.10.10.2/24' )
    net.addLink( root, bgp )

    for i in range(1,3+1):
        sdn_h.append(net.addHost('sdn_h%s' % i, cls=SdnIpHost, ip="10.0.100.%s/24" % i, route="10.0.100.254"))
    
    """   
    sdn_h1 = net.addHost('sdn_h1', cls=SdnIpHost, ip="10.100.10.1/24", route="10.100.10.101")
    sdn_h2 = net.addHost('sdn_h2', cls=SdnIpHost, ip="10.100.10.2/24", route="10.100.10.101")
    sdn_h3 = net.addHost('sdn_h3', cls=SdnIpHost, ip="10.100.10.3/24", route="10.100.10.101")
    """
     
    net.addLink(sdn_s[5], sdn_h[0])
    net.addLink(sdn_s[5], sdn_h[1])
    net.addLink(sdn_s[5], sdn_h[2])
    
    for i in range(len(sdn_h)):
        sdn_h[i].cmd('ifconfig '+sdn_h[i].name+'-eth0 inet6 add 2001:100::%s/64 up' % (i+1))
        sdn_h[i].cmd('route -A inet6 add default gw 2001:100::254')
    
    # Wire up the switches in the topology
    net.addLink( sdn_s[0], sdn_s[2] )
    net.addLink( sdn_s[0], sdn_s[4] )
#    net.addLink( sdn_s[2], sdn_s[4] )
    net.addLink( sdn_s[2], sdn_s[5] )
    net.addLink( sdn_s[4], sdn_s[1] )
    net.addLink( sdn_s[4], sdn_s[5] )
#    net.addLink( sdn_s[5], sdn_s[1] )
    net.addLink( sdn_s[5], sdn_s[3] )
    net.addLink( sdn_s[1], sdn_s[3] )
    
#    for i in range(len(sdn_s)):
#        subprocess.call(["ovs-vsctl", "set", "bridge sdn_s%s" % (i+1), "protocols = OpenFlow13"])

if __name__ == '__main__':
    global isp_h, isp_s, sdn_h, sdn_s, gwr
    setLogLevel('debug')
    net = Mininet(topo=None, controller=RemoteController)
    onos = net.addController("onos",
                      controller=RemoteController, link=TCLink,
                      ip=REMOTE_CONTROLLER_IP, port=6633)
    
    createSoDIP6Network(net)

    net.start()

    CLI(net)

    net.stop()

    info("done\n")
