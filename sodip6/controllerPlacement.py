# Program code for Multi-domain SoDIP6 network implementation using ONOS/SDN-IP
__author__ = "Babu R Dawadi - baburd"
__copyright__ = "Copyright 2020, The SoDIP6 Project"
__credits__ = ["GRC Lab @UPV", "LICT lab @IOE-TU", "NTNU-MSESSD",
                    "CARD @IOE-TU"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Babu R Dawadi"
__email__ = "baburd@ioe.edu.np"
__status__ = "Test/Implementation"

import math
from sodip6.graphs import PlotGraphs, HandlerCircle
from OptimalPathV3 import optimal_path
import xlsxwriter
import random


def BFTravel(spList):
    subGraph = {}
    queue = []
    visited = []
    spList.pop()
    spList.pop(0)
    #print(spList)
    median_point = math.ceil((len(spList)) / 2)-1
    rss_switch = spList[median_point]
    subGraph[spList[median_point]] = [spList[median_point-1],spList[median_point+1]]
    for nd in range(median_point-1,-1,-1):
        subGraph[spList[nd]] = [spList[nd - 1]]
    for nd in range(median_point+1,len(spList)-1):
        subGraph[spList[nd]] = [spList[nd + 1]]
    subGraph[spList[0]] = []
    subGraph[spList[-1]] = []

    visited.append(rss_switch)
    queue.append(rss_switch)
    bft_list = []
    while queue:
        s = queue.pop(0)
        bft_list.append(s)
        for neighbour in subGraph[s]:
            if neighbour not in visited:
                visited.append(neighbour)
                queue.append(neighbour)
    return bft_list


def migrate_without_bft(G, g, valid_sp_list):
    plot_latency = PlotGraphs()
    #set all routers into unmigrated list
    for rtr in g.vert_dict.keys():
        g.get_router(rtr).set_migration(SoDIP6=False)

    #for i in range(1, len(valid_sp_list[0])-1):
    print(valid_sp_list[0])

    #migrate rss fisrt to swhitch
    rss = valid_sp_list[0][5]
    #g.get_router(rss).set_migration(SoDIP6=True)
    #g.get_router(rss).set_type(type='S')
    print('rss:',rss)

    latency_switch_list = []
    latency_gateway_list = []
    for j in range (len(valid_sp_list)):
        for bft in valid_sp_list[j]:
            #print(valid_sp_list[j])
            print(bft, g.get_router(bft).get_type())
            if g.get_router(bft).get_migration() is False and g.get_router(bft).get_type() in ['R', 'SG']:
                g.get_router(bft).set_migration(SoDIP6=True)
                g.get_router(bft).set_type(type = 'S')
                print('Rotuer '+bft+' is migrated')
                neighbor_switch = g.get_router(bft).get_neighbors()
                for sdns in neighbor_switch:
                    if sdns.get_type() is 'R':
                        sdns.set_type(type='SG')
                migrated_nodes = g.get_switch_list()
                latency_switch = 0.0
                for sdn_switch in migrated_nodes:
                    pcost, nds = optimal_path(g, sdn_switch, rss)
                    pcost = pcost if pcost is not None else 0.0
                    latency_switch = latency_switch + (pcost+10.0)/100
                latency_switch_list.append([len(migrated_nodes),round(latency_switch,3)])

                switch_gw_nodes = g.get_switch_gateways()
                latency_gateway = 0.0
                for switch_gw in switch_gw_nodes:
                    pcost, nds = optimal_path(g, switch_gw, rss)
                    pcost = pcost if pcost is not None else 0.0
                    latency_gateway = latency_gateway + float ((pcost + 10.0) / 100)
                latency_gateway_list.append([len(switch_gw_nodes), round(latency_gateway,3)])

    for rtr in g.get_routers_list():
        g.get_router(rtr).set_migration(SoDIP6=True)
        g.get_router(rtr).set_type(type='S')
    migrated_nodes = g.get_switch_list()
    latency_switch = 0.0
    for sdn_switch in migrated_nodes:
        pcost, nds = optimal_path(g, sdn_switch, rss)
        pcost = pcost if pcost is not None else 0.0
        latency_switch = latency_switch + (pcost + 10.0) / 100
    latency_switch_list.append([len(migrated_nodes), round(latency_switch, 3)])

    switch_ext_nodes = g.get_external_gateways()
    latency_gateway = 0.0
    for switch_gw in switch_ext_nodes:
        pcost, nds = optimal_path(g, switch_gw, rss)
        pcost = pcost if pcost is not None else 0.0
        latency_gateway = latency_gateway + float((pcost + 10.0) / 100)
    latency_gateway_list.append([len(switch_ext_nodes), round(latency_gateway, 3)])

    if latency_switch_list:
        workbook = xlsxwriter.Workbook('Latency_without_BFTRSS_%s.xlsx' %rss)
        switch_sheet = workbook.add_worksheet('Switch_Latency')
        for row_num, data in enumerate(latency_switch_list):
            switch_sheet.write_row(row_num, 0, data)

        gateway_sheet = workbook.add_worksheet('Gateway_Latency')
        for row_num, data in enumerate(latency_gateway_list):
            gateway_sheet.write_row(row_num, 0, data)
        workbook.close()
        plot_latency.plot_latency_sp(latency_switch_list,latency_gateway_list)
    #if latency_gateway_list:
        #plot_latency.plot_latency_gateway(latency_gateway_list)
#plot_latency.plot_with_controller(G, g)

def migrate_with_bft(G, g, valid_sp_list):
    plot_latency = PlotGraphs()
    #set all routers into unmigrated list
    for rtr in g.vert_dict.keys():
        g.get_router(rtr).set_migration(SoDIP6=False)

    valid_bft_list = BFTravel(valid_sp_list[0])
    print(valid_bft_list)

    #migrate the RSS firt to switch
    rss = valid_bft_list[0]
   #g.get_router(rss).set_migration(SoDIP6=True)
    #g.get_router(rss).set_type(type='S')

    print('rss:',rss)
    latency_switch_list = []
    latency_gateway_list = []
    controller_load_list = []

    cotroller_capacity = 1.5

    for j in range (len(valid_sp_list)):
        for bft in BFTravel(valid_sp_list[j]):
            print(valid_bft_list)
            print(bft, g.get_router(bft).get_type())
            switch_request = random.randint(50, 105) / 1000  # min 0.05K to max 0.105K request per second
            gateway_request = random.randint(10, 20) / 1000  # max 0.02K request per second
            if g.get_router(bft).get_migration() is False and g.get_router(bft).get_type() in ['R', 'SG']:
                g.get_router(bft).set_migration(SoDIP6=True)
                g.get_router(bft).set_type(type = 'S')
                print('Router '+bft+' is migrated')
                neighbor_switch = g.get_router(bft).get_neighbors()
                for sdns in neighbor_switch:
                    if sdns.get_type() is 'R':
                        sdns.set_type(type='SG')
                migrated_nodes = g.get_switch_list()
                latency_switch = 0.0
                for sdn_switch in migrated_nodes:
                    pcost, nds = optimal_path(g, sdn_switch, rss)
                    pcost = pcost if pcost is not None else 0.0
                    latency_switch = latency_switch + (pcost+10.0)/100
                latency_switch_list.append([len(migrated_nodes),round(latency_switch,3)])

                switch_gw_nodes = g.get_switch_gateways()
                latency_gateway = 0.0
                for switch_gw in switch_gw_nodes:
                    pcost, nds = optimal_path(g, switch_gw, rss)
                    pcost = pcost if pcost is not None else 0.0
                    latency_gateway = latency_gateway + float ((pcost + 10.0) / 100)
                latency_gateway_list.append([len(switch_gw_nodes), round(latency_gateway,3)])
                controller_load_list.append([len(switch_gw_nodes)+len(migrated_nodes), len(migrated_nodes) * switch_request+len(switch_gw_nodes) *
                                             gateway_request])

    for rtr in g.get_routers_list():
        g.get_router(rtr).set_migration(SoDIP6=True)
        g.get_router(rtr).set_type(type='S')
    migrated_nodes = g.get_switch_list()
    latency_switch = 0.0
    for sdn_switch in migrated_nodes:
        pcost, nds = optimal_path(g, sdn_switch, rss)
        pcost = pcost if pcost is not None else 0.0
        latency_switch = latency_switch + (pcost + 10.0) / 100
    latency_switch_list.append([len(migrated_nodes), round(latency_switch, 3)])

    switch_ext_nodes = g.get_external_gateways()
    latency_gateway = 0.0
    for switch_gw in switch_ext_nodes:
        pcost, nds = optimal_path(g, switch_gw, rss)
        pcost = pcost if pcost is not None else 0.0
        latency_gateway = latency_gateway + float((pcost + 10.0) / 100)
    latency_gateway_list.append([len(switch_ext_nodes), round(latency_gateway, 3)])

    controller_load_list.append([len(switch_ext_nodes)+len(migrated_nodes), len(migrated_nodes) * switch_request +
                                 len(switch_ext_nodes) * gateway_request])

    if latency_switch_list:
        workbook = xlsxwriter.Workbook('Latency_with_BFTRSS_%s.xlsx' %rss)
        switch_sheet = workbook.add_worksheet('Switch_Latency')
        for row_num, data in enumerate(latency_switch_list):
            switch_sheet.write_row(row_num, 0, data)

        gateway_sheet = workbook.add_worksheet('Gateway_Latency')
        for row_num, data in enumerate(latency_gateway_list):
            gateway_sheet.write_row(row_num, 0, data)

        controller_sheet = workbook.add_worksheet('Controller_load')
        for row_num, data in enumerate(controller_load_list):
            controller_sheet.write_row(row_num, 0, data)

        #controller_sheet.write_column(1, 0, controller_load_list)
        workbook.close()

        plot_latency.plot_latency_sp(latency_switch_list,latency_gateway_list)
    #if latency_gateway_list:
        #plot_latency.plot_latency_gateway(latency_gateway_list)
#plot_latency.plot_with_controller(G, g)

def set_migration_as(G, g, sp_list,rss):
    bgps = 'ONOS-BGP'
    G.add_node(bgps)
    G.add_edge(rss, bgps, weight=10.0)
    g.add_edge(rss, bgps, weight=10.0)

    #migrate median router to RSS ans
    #g.get_router(rss).set_migration(SoDIP6=True)
    #g.get_router(rss).type = "RSS"
    g.get_router(bgps).set_migration(SoDIP6=True)
    g.get_router(bgps).type = "BGPS" #BGP speaker

    #migrate_without_bft(G,g,sp_list)
    migrate_with_bft(G, g, sp_list)
