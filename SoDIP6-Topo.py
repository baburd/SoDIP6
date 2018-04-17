__author__ = 'babu'

"""
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

topos = { 'sodip6topo': ( lambda: SoDIP6Topo() )}

def runSoDIP6():
    # Create and test a simple network
    # topo = SoDIP6Topo()
    net = Mininet(topo=None,controller=None)
    net.addController("c0",
                      controller=RemoteController,
                      ip=REMOTE_CONTROLLER_IP,
                      port=6633)
    s = []
    h = []

    info('*** Adding Switches\n')
    for i in range(16):
        s.append(net.addSwitch('s%s' %i, protocols='OpenFlow13'))
    #net.delSwitch(s[0])

    # adding Hosts
    info('*** Adding Hosts\n')
    for i in range(8):
        h.append(net.addHost('h%s' %i))
    #adding link among switch and hosts
    info('*** Creating Links\n')
    net.addLink(s[1], s[2])            #link between router 1 to 2
    net.addLink(s[1], s[3])
    net.addLink(s[1], s[7])
    net.addLink(s[1], s[14])
    net.addLink(s[2], s[6])
    net.addLink(s[3], s[4])
    net.addLink(s[4], s[5])
    net.addLink(s[4], s[6])
    net.addLink(s[4], s[8])
    net.addLink(s[4], s[9])
    net.addLink(s[5], s[8])
    net.addLink(s[6], s[7])
    net.addLink(s[7], s[9])
    net.addLink(s[7], s[10])
    net.addLink(s[8], s[11])
    net.addLink(s[9], s[11])
    net.addLink(s[9], s[12])
    net.addLink(s[9], s[13])
    net.addLink(s[10], s[13])
    net.addLink(s[10], s[15])
    net.addLink(s[14], s[15])          #link between router 14 and router 15

    net.addLink(h[1], s[3])            #link between host 1 and router 3 -- wireline home user H1
    net.addLink(h[2], s[3])            # wireless home user -- h2
    net.addLink(h[3], s[5])            #bank --h3
    net.addLink(h[4], s[8])            #city office -- h4
    net.addLink(h[5], s[11])           #unviersity -- h5
    net.addLink(h[6], s[13])           # Govt. Office -- h6
    net.addLink(h[7], s[15])           #NGOsINGOs -- h7
    net.addLink(h[0],s[1])             # host 0 id the NCR host connected with Central router S1

        #addign ip address to all host machine
    info('*** Starting Networks\n')
    net.start()

    h[0].cmd('ifconfig h0-eth0 10.100.100.1 netmask 255.255.255.0 up')
    h[0].cmd('ifconfig h0-eth0 inet6 add 2001:DB8:1212::1/64 up')

    h[1].cmd('ifconfig h1-eth0 10.100.100.9 netmask 255.255.255.0 up')
    h[1].cmd('ifconfig h1-eth0 inet6 add 2001:DB8:1212::9/64 up')

    h[2].cmd('ifconfig h2-eth0 10.100.100.17 netmask 255.255.255.0 up')
    h[2].cmd('ifconfig h2-eth0 inet6 add 2001:DB8:1212::17/64 up')

    h[3].cmd('ifconfig h3-eth0 10.100.100.25 netmask 255.255.255.0 up')
    h[3].cmd('ifconfig h3-eth0 inet6 add 2001:DB8:1212::25/64 up')

    h[4].cmd('ifconfig h4-eth0 10.100.100.33 netmask 255.255.255.0 up')
    h[4].cmd('ifconfig h4-eth0 inet6 add 2001:DB8:1212::33/64 up')

    h[5].cmd('ifconfig h5-eth0 10.100.100.41 netmask 255.255.255.0 up')
    h[5].cmd('ifconfig h5-eth0 inet6 add 2001:DB8:1212::41/64 up')

    h[6].cmd('ifconfig h6-eth0 10.100.100.49 netmask 255.255.255.0 up')
    h[6].cmd('ifconfig h6-eth0 inet6 add 2001:DB8:1212::49/64 up')

    h[7].cmd('ifconfig h7-eth0 10.100.100.57 netmask 255.255.255.0 up')
    h[7].cmd('ifconfig h7-eth0 inet6 add 2001:DB8:1212::57/64 up')

    print ("Dumping host connections")
    dumpNodeConnections(net.hosts)
    print ("Testing network connectivity")
    #net.pingAll()
    CLI(net)
    net.stop()

# if the script is run directly (sudo custom/optical.py):
if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    runSoDIP6()
