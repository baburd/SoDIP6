__author__ = 'babu'

"""
This is the custom topology for SDN and IPv6 functionality test with evaluation of energy consumption over \
mininet-wifi with ODL SDN contrller
This topology has
    number of switch = 14 including number of base station(Access Points) =3
    number of links = 24 including root host link used for traffic tests
    number of CPEs=7 including number of wifi stations=2
    hosts are recognized as CPE of individual users and enterprises     
"""

from mininet.log import setLogLevel, info
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.util import dumpNodeConnections


import schedule,functools
import time, datetime
#import csv

from mn_wifi.cli import CLI_wifi
from mn_wifi.net import Mininet_wifi
import re, subprocess
import threading

global net, h, s, pnode, hv6addr



REMOTE_CONTROLLER_IP = "192.168.56.101"


class OVSBridgeSTP(OVSSwitch):
    """Open vSwitch Ethernet bridge with Spanning Tree Protocol
       rooted at the first bridge that is created"""
    prio = 1000

    def start(self, *args, **kwargs):
        OVSSwitch.start(self, *args, **kwargs)
        OVSBridgeSTP.prio += 1
        self.cmd('ovs-vsctl set-fail-mode', self, 'standalone')
        self.cmd('ovs-vsctl set-controller', self)
        self.cmd('ovs-vsctl set Bridge', self,
                 'stp_enable=true',
                 'other_config:stp-priority=%d' % OVSBridgeSTP.prio)


switches = {'ovs-stp': OVSBridgeSTP}


class NodePower():
    def __init__(self, name='s0', type='switch',status='active'):
        self.name=name
        self.type=type
        self.status=status
        self.pSwitchActive=110
        self.pLinkActive=40
        self.pmbpsActive=0.01

        self.pSwitchSleep = 33
        self.pLinkSleep = 0.0
        self.pmbpsSleep = 0.0

        self.pCPEActive = 7

        self.pCPESleep = 2.1
        self.pCPElinkSleep = 0.0

    def setActivePower(self, pActive=110,pLinkActive=40):
        if self.type=='CPE':
            self.pCPEActive=pActive
            self.pCPELinkActive=pLinkActive
        else:
            self.pSwitchActive=pActive
            self.pLinkActive=pLinkActive


    def setSleepPower(self,pSleep=33, pLinkSleep=0.0):
        if self.type=='CPE':
            self.pCPESleep=pSleep
            self.pCPElinkSleep=pLinkSleep
        else:
            self.pSwitchSleep=pSleep
            self.pLinkSleep=pLinkSleep


    def getPower(self):
        if self.status == 'sleep':
            return self.pCPESleep if self.name.startswith("cpe") else self.pSwitchSleep

        if self.type=='CPE':
            return self.pCPEActive+0.01
        else:
            cmd = ['sudo ovs-vsctl list-ports '+self.name]
            ifaces=subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE).stdout.read().splitlines()
            #print(ifaces)
            return self.pSwitchActive + self.getPortsPower(ifaces)


    def getSleepPower(self):
        if self.type=='CPE':
            return self.pCPESleep
        else:
            return self.pSwitchSleep


    def getPortsPower(self,ifaces):
        pvalue=0.0
        for iface in ifaces:
            cmd = ['sudo vnstat -tr 3 -s -i '+iface]
            speed=re.search('tx (.+?)bit/s', \
                            subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE).stdout.read().format()).group(0)
            thruput=(speed[2:].strip()).split()
            if thruput[1]=='kbit/s':
                piface=float(thruput[0])/1000*0.05 + 0.01
            else:
                piface=float(thruput[0])*0.05 + 0.01
            print("Avg. thruput of "+iface+" is:" + str(thruput[0]) +" " + thruput[1])
            pvalue+=piface
        return pvalue

    def getLinkActive(self):
        return self.pLinkActive

    def getLinkSleep(self):
        return self.pLinkSleep

    def hasTraffic(self):
        if self.type == 'switch':
            cmd = ['sudo vnstat -tr 3 -s -i ' + self.name]
            print(cmd)
            speed = re.search('tx (.+?)bit/s', \
                              subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read().format()).group(0)
            thruput = (speed[2:].strip()).split()
            return True if float(thruput[0]) > 0.00 else False
        elif self.type == 'CPE':
            diface = net.get(self.name).intf().name
            cmdstr = 'vnstat -tr 3 -s -i ' + diface
            rslt = net.get(self.name).cmd(cmdstr).format().strip()
            # rslt = re.sub('\n^\s+\n$', '\n', rslt)
            speedtx = re.search('tx (.+?)bit/s', rslt, re.MULTILINE).group(0)
            thrupcpe = (speedtx[2:].strip()).split()
            return True if float(thrupcpe[0]) > 0.00 else False
        else:
            print("wrong node type")
            return


    def setStatus(self,status):
        self.status = status


    def getStatus(self):
        return self.status


    def getName(self):
        return self.name


class ScheduleThread(threading.Thread):
    @staticmethod
    def run():
        while True:
            schedule.run_pending()
            time.sleep(60)



def with_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print('LOG: Running job "%s"' % func.__name__)
        result = func(*args, **kwargs)
        print('LOG: Job "%s" completed' % func.__name__)
        return result
    return wrapper


def createNetwork(net):
    info("***adding access switches and base stations\n")
    for i in range(11):
        s.append(net.addSwitch('s%s' % i))
        pnode.append(NodePower(name='s%s' % i, type='switch', status='active'))

    s.append(net.addAccessPoint('ap1', ssid='AP1SSID', mode='g', channel='1', position='45,40,0', range=40))
    pnode.append(NodePower(name='ap1', type='switch', status='active'))
    s.append(net.addAccessPoint('ap2', ssid='AP2SSID', mode='g', channel='5', position='90,40,0', range=20))
    pnode.append(NodePower(name='ap2', type='switch', status='active'))
    s.append(net.addAccessPoint('ap3', ssid='AP3SSID', mode='g', channel='6', position='80,40,0', range=30))
    pnode.append(NodePower(name='ap3', type='switch', status='active'))

    for shw in s:
        print(shw)

    info("*** adding hosts and stations\n")
    for i in range(5):
        h.append(net.addHost('cpe%s' % i))
        pnode.append(NodePower(name='cpe%s' % i, type='CPE', status='active'))

        # net.plotNode(h[i],position=str(i*5+5)+','+str(i*5+5)+',0')
    outNet = net.addHost('outNet')  # outere edge network to metro network connection gateway

    h.append(net.addStation('cpe5'))
    pnode.append(NodePower(name='cpe5', type='CPE', status='active'))
    h.append(net.addStation('cpe6'))
    pnode.append(NodePower(name='cpe6', type='CPE', status='active'))
    h.append(net.addStation('cpe7'))
    pnode.append(NodePower(name='cpe7', type='CPE', status='active'))

    net.configureWifiNodes()
    # net.plotGraph(max_x=200,max_y=200)

    # adding link among switch and hosts
    net.addLink(s[0], s[1])
    net.addLink(s[0], s[2])
    net.addLink(s[1], s[3])
    net.addLink(s[1], s[4])
    net.addLink(s[1], s[5])
    net.addLink(s[2], s[3])
    net.addLink(s[2], s[4])
    net.addLink(s[2], s[5])
    net.addLink(s[3], s[6])
    net.addLink(s[3], s[7])
    net.addLink(s[3], s[8])
    net.addLink(s[4], s[9])
    net.addLink(s[4], s[10])
    net.addLink(s[4], s[11])
    net.addLink(s[5], s[12])
    net.addLink(s[5], s[13])

    # addin hosts link
    net.addLink(h[0], s[6], bw=5)
    net.addLink(h[1], s[7], bw=5)
    net.addLink(h[2], s[8], bw=5)
    net.addLink(h[3], s[9], bw=5)
    net.addLink(h[4], s[10], bw=5)
    net.addLink(h[5], s[11], bw=5)
    net.addLink(h[6], s[12], bw=5)
    net.addLink(h[7], s[13], bw=5)

    net.addLink(outNet, s[0], bw=1000)


def setIPv6Address(net):
    #setting global unciast IPv6 address to all hosts/stations
    v6Addr = 1
    for cpe in h:
        cpeiface=cpe.intf().name
        setV6Addr = 'ifconfig ' + cpeiface +' inet6 add 2001:DB8:1212::'+ str(v6Addr) +'/64 up'
        cpe.cmd(setV6Addr)
        hv6addr.append('2001:DB8:1212::'+ str(v6Addr))
        v6Addr +=8

    net.get('outNet').cmd('ifconfig outNet-eth0 inet6 add 2001:DB8:1212::'+str(v6Addr)+'/64 up')
    hv6addr.append('2001:DB8:1212::'+str(v6Addr))

    cmdstr = 'iperf -V -s -u -B 2001:DB8:1212::65 &'
    net.get('outNet').popen(cmdstr,shell=True)


@with_logging
def genIPv6Traffic():
    tmhr = datetime.datetime.now().hour
    if 5 <= tmhr < 22:
        cmd = 'iperf -u -t 20 -i 1 -V -c ' + hv6addr[len(hv6addr) - 1] + ' &'
        print('Generating IPv6 traffic from cpe 1,3,5,7 to OutNet....'+hv6addr[len(hv6addr) - 1])
        for i in range(1,len(h),2):
            h[i].popen(cmd, shell=True)


@with_logging
def genPing6Traffic():
    tmhr = datetime.datetime.now().hour
    if 5 <= tmhr < 22:
        h[1].popen('ping6 -c 30 ' + hv6addr[7], shell=True)
        h[2].popen('ping6 -c 30 ' + hv6addr[5], shell=True)
        h[0].popen('ping6 -c 30 ' + hv6addr[6], shell=True)
        h[3].popen('ping6 -c 30 ' + hv6addr[8], shell=True)
        h[4].popen('ping6 -c 30 ' + hv6addr[8], shell=True)


@with_logging
def recordSwitchPower():
    with open('recSwitchPower.csv', mode='a+') as pfile, open('recSwitchTotPower.csv', mode='a+') as pfile1:
        totPower = 0.0
        for pd in pnode:
            tm=datetime.datetime.now()
            spower =pd.getPower()
            totPower += spower
            pdata = pd.name + ',' + str(tm.hour) +':'+str(tm.minute) + ',' + str(spower)+"\n"
            pfile.write(pdata)
            print('Power recorded for '+pd.getName()+'....' + pdata)
        pdata = str(tm.hour) + ':' + str(tm.minute) + ',' + str(totPower) + "\n"
        pfile1.write(pdata)
        print('test bed total power status' + '....' + pdata)
        pfile.close()
        pfile1.close()


@with_logging
def recordLinkPower():
    plink=0.0
    with open('recLinkPower.csv', mode='a+') as pfile:
        for link in net.links[:-1]:
            devlink=str(link)[:str(link).index('-')]
            nd=int(re.findall('\d+',devlink)[0])
            if devlink.startswith("cpe"):
                nd+=len(s)
            plink+=pnode[nd].getLinkSleep() if pnode[nd].getStatus()=='sleep' else pnode[nd].getLinkActive()
            tm = datetime.datetime.now()
        pdata = str(tm.hour) + ':' + str(tm.minute) + ',' + str(plink) + "\n"
        pfile.write(pdata)
        print('Power recorded for all 24 links:'+ pdata)


    # headers = "Device, time, energy\n"
    #
    # with open('recLinkPower.csv', mode='a+') as pfile:
    #     #pfile.write(headers)
    #     for pd in pnode:
    #         tm=datetime.datetime.now()
    #         pdata = pd.name + ',' + str(tm.hour) +':'+str(tm.minute) + ',' + str(getLinkPower())+"\n"
    #         pfile.write(pdata)
    #         print('Power recorded for '+pd.getName()+'....' + pdata)
    #
    # pfile.close()

@with_logging
def makeSleepAll():
    for nd in range(len(s)):
        cmd = ['sudo ovs-vsctl list-ports ' + s[nd].name]
        ifaces = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read().splitlines()
        trSleep = True
        for iface in ifaces:
            cmd = ['sudo vnstat -tr 3 -s -i ' + iface]
            speedtx = re.search('tx (.+?)bit/s', \
                        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read().format()).group(0)

            thruput = (speedtx[2:].strip()).split()
            if float(thruput[0]) < 0.221 and thruput[1]=='kbit/s':
                print("interface " + iface + " has only signaling traffic, shutting down.....")
            else:
                print("interface " + iface + " has  real traffic:" + str(thruput[0]) + " " + thruput[1])
                trSleep = False

        if trSleep:
            print("Mode of " + pnode[nd].getName() + " is:" + pnode[nd].getStatus() + \
                  " and only signaling traffic on its interfaces...sleeping...")
            pnode[nd].setStatus(status='sleep')
        else:
            print('Mode of '+pnode[nd].getName() + ' is set to active...')
            pnode[nd].setStatus(status='active')

    for cpe in h:
        trSleep = True
        cpeiface=cpe.intf().name
        cmdstr = 'vnstat -tr 3 -s -i ' + cpeiface
        print(cmdstr)
        rslt = cpe.cmd(cmdstr).format().strip()
        # rslt = re.sub('\n^\s+\n$', '\n', rslt)
        speedtx = re.search('tx (.+?)bit/s', rslt, re.MULTILINE).group(0)
        thruput = (speedtx[2:].strip()).split()
        if float(thruput[0]) > 0.22 and thruput[1] == 'kbit/s':
            print("interface " + cpeiface + " has  real traffic:" + str(thruput[0]) + " " + thruput[1])
            trSleep = False
        pos = len(s) + int(cpe.name[3:])
        if trSleep:
            print("Mode of " + cpe.name + " is:" + pnode[pos].getStatus() + \
                  " and only signalling traffic on its interfaces...sleeping...")
            pnode[pos].setStatus(status='sleep')
        else:
            print(cpe.name + ' is set to active...')
            pnode[pos].setStatus(status='active')

@with_logging
def wakeupall():
    for snode in pnode:
        if snode.hasTraffic and snode.getStatus()=='sleep':
                print("Activating node: " + snode.getName())
                snode.setStatus(status='active')
        else:
            print('Device: ' + snode.getName() + ' has no traffic ...skipping')


def runSoDIP6():
    #create Rural End Access network with wifi capability
    #topo.set_ovs_protocol_13()
    global h, s, pnode, hv6addr, net
    net = Mininet_wifi(controller=RemoteController, link=TCLink)
    c1=net.addController("c1",controller=RemoteController,ip=REMOTE_CONTROLLER_IP,port=6633)

    s = []
    h = []
    hv6addr = []
    pnode = []

    createNetwork(net)

    info("***Starting network..")
    net.build()
    c1.start()
    for switchall in s:
        switchall.start([c1])

    setIPv6Address(net)
    #print(net.hosts(sort=True))

    info("***Dumping host connections\n")
    dumpNodeConnections(s)
    dumpNodeConnections(h)

#below functions are all for the customized mininet commands

    def sleepnode(self,*arg):
        #run the thread to sleep switch after checking its status.

        if arg[0] == "":
            makeSleepAll()
        else:
            nodep = int(re.findall(r'\d+', arg[0]).pop())
            if arg[0].startswith('cp'):
                nodep += len(s)
            if pnode[nodep].getStatus()=='sleep':
                print("Device "+ arg[0] +" already in sleep mode .. skipping...")
                return

            pnode[nodep].setStatus(status='sleep')
            print("device: "+pnode[nodep].getName()+" entered into force sleep")
            time.sleep(2)


    def pmon(self,*arg):
        if arg[0] =="":
            for nd in range(len(s)):
                print("Mode of " + s[nd].name + " is:" + pnode[nd].getStatus() + " current power consumption is: "+ \
                      str(pnode[nd].getPower()) + " Watts")
            for nd in range(len(h)):
                print('Mode of cpe%s'%nd + ' is:' + pnode[nd].getStatus()+" current power is:" + \
                      str(pnode[nd].getPower()) + " Watts")
        else:
            nodep = int(re.findall(r'\d+',arg[0]).pop())
            if arg[0].startswith('cp'):
                nodep +=len(s)
            print("Mode of "+arg[0]+" is:"+ pnode[nodep].getStatus()+" Power is: "+ \
                  str(pnode[nodep].getPower())+" Watts")


    def ping6all(self,*arg):
        print("ping for ipv6 connectivity test")
        bck = '' if arg[0]=='' else ' &'
        for hst in h:
            for v6haddr in hv6addr:
                print(hst.cmd('ping6 -c 2 ' + v6haddr+' '+bck))


    def wakeupnode(self,*arg):
        if arg[0] == "":
            wakeupall()
        else:
            nodep = int(re.findall(r'\d+', arg[0]).pop())
            if arg[0].startswith('cp'):
                nodep += len(s)
            if pnode[nodep].getStatus()=='sleep' and pnode[nodep].hasTraffic():
                pnode[nodep].setStatus(status='active')
                print("Device:"+pnode[nodep].getName()+" is waking up...")
            else:
                print('Device: ' + pnode[nodep].getName() + ' has no traffic ...skipping')

        time.sleep(2)


    def linkp(self, *arg):
        threading.Thread(target=recordLinkPower).start()
        # links = net.links
        # for link in links:
        #     for lnk in link.intf():
        #         print(lnk)
        #         lnk.config(up=False)

    CLI_wifi.do_pmon = pmon
    CLI_wifi.do_ping6all = ping6all
    CLI_wifi.do_sleepnode = sleepnode
    CLI_wifi.do_wakeupnode = wakeupnode
    CLI_wifi.do_linkp = linkp

    make_sleep_thread = ScheduleThread()
    make_sleep_thread.daemon=True
    make_sleep_thread.start()


    def genIPv6Traffic_thread():
        threading.Thread(target = genIPv6Traffic).start()
    def makeSleepAll_thread():
        threading.Thread(target = makeSleepAll).start()
    def recordSwitchPower_thread():
        threading.Thread(target=recordSwitchPower).start()
    def recordLinkPower_thread():
        threading.Thread(target=recordLinkPower).start()
    def genPing6Traffic_thread():
        threading.Thread(target=genPing6Traffic).start()

    schedule.every(2).minutes.do(genIPv6Traffic_thread).tag('per-tasks', 'generate-IPv6-traffic')
    schedule.every(2).to(4).minutes.do(makeSleepAll_thread).tag('per-tasks','sleep-node')
    schedule.every(2).to(3).minutes.do(recordSwitchPower_thread).tag('per-tasks','measure-switch-power')
    schedule.every(2).to(3).minutes.do(recordLinkPower_thread).tag('per-tasks','measure-link-power')
    schedule.every(3).minutes.do(genPing6Traffic_thread).tag('per-tasks','generate-IPv6-traffic')
    schedule.every().day.at("06:00").do(wakeupall).tag('per-tasks','wakeup-all-sleep-nodes')


    CLI_wifi(net)
    info("***Stopping Networks\n")
    net.stop()
    schedule.clear('per-tasks')

# if the script is run directly (sudo custom/optical.py):
if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    runSoDIP6()
