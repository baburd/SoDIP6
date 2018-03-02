__author__ = 'babu'

"""
Synchronized to GitHub
This is the custom topology created by baburd to test IPv6 functionality over mininet with SDN contrller
This topology has
    number of switch = 15
    number of links > 22
    number of hosts = hosts are recognized as sub network or single host machine     
"""

from mininet.node import CPULimitedHost
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.util import dumpNodeConnections

REMOTE_CONTROLLER_IP = "192.168.56.101"

class SoDIP6Topo(Topo):
    def __init__(self, **opts):
        # Initialize topology and default optioe
        Topo.__init__(self, **opts)
        s = []
        h = []
        s.append('NULL')
        h.append('NULL')

        for i in range(15):
            s.append(self.addSwitch('s%s' %(i+1), protocols='OpenFlow13'))

        # adding Hosts
        for i in range(7):
            h.append(self.addHost('h%s' %(i+1)))

        #adding link among switch and hosts
        self.addLink(s[1], s[2])
        self.addLink(s[1], s[3])
        self.addLink(s[1], s[7])
        self.addLink(s[1], s[14])
        self.addLink(s[2], s[6])
        self.addLink(s[3], s[4])
        self.addLink(s[4], s[5])
        self.addLink(s[4], s[6])
        self.addLink(s[4], s[8])
        self.addLink(s[4], s[9])
        self.addLink(s[5], s[8])
        self.addLink(s[6], s[7])
        self.addLink(s[7], s[9])
        self.addLink(s[7], s[10])
        self.addLink(s[8], s[11])
        self.addLink(s[9], s[11])
        self.addLink(s[9], s[12])
        self.addLink(s[9], s[13])
        self.addLink(s[10], s[13])
        self.addLink(s[10], s[15])
        self.addLink(s[14], s[15])

        #addin hosts link
        self.addLink(h[1], s[3])
        self.addLink(h[2], s[3])
        self.addLink(h[3], s[5])
        self.addLink(h[4], s[8])
        self.addLink(h[5], s[11])
        self.addLink(h[6], s[13])
        self.addLink(h[7], s[15])


def runSoDIP6():
    # Create and test a simple network
    topo = SoDIP6Topo()

    net = Mininet(topo=topo,
                  controller=None)
    net.addController("c0",
                      controller=RemoteController,
                      ip=REMOTE_CONTROLLER_IP,
                      port=6633)
    net.start()
    print ("Dumping host connections")
    dumpNodeConnections(net.hosts)
    print ("Testing network connectivity")
    #net.pingAll()
    net.stop()

# if the script is run directly (sudo custom/optical.py):
if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    runSoDIP6()
