import networkx as nx  # this is used for graph visualization
import matplotlib.pyplot as plt  # matlabb plotting and visualizations
import matplotlib.image as pimg
from matplotlib.legend_handler import HandlerPatch  # for manual drawind of legend
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd,csv

class HandlerCircle(HandlerPatch):
    # def __init__(self):
    # self.radius=radius
    def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans):
        center = 0.5 * width - 0.5 * xdescent, 0.5 * height - 0.5 * ydescent
        p = mpatches.Circle(xy=center, radius=8)
        self.update_prop(p, orig_handle, legend)
        p.set_transform(trans)
        return [p]

class PlotGraphs:
    def __init__(self):
        pass

    def plot_graph(self ,G, shortest_path, shortest_edges, mg_list=[]):
        pos = nx.spring_layout(G)  # positions for all nodes
        plt.subplot(1, 2, 1)
        nx.draw_networkx_nodes(G, pos, node_color='red', node_size=280)
        # edges
        nx.draw_networkx_edges(G, pos, width=3, alpha=0.5, edge_color='r')
        nx.draw_networkx_labels(G, pos, font_size=8, font_family='sans-serif')
        edge_cost = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_cost,font_size=8, font_family='sans-serif')
        # labels

        plt.axis('off')
        plt.title('Software Defined IPv6 Network Optimal Path Finding')
        plt.plot()

        plt.subplot(1, 2, 2)

        colors = []
        for node in G.nodes():
            if node in mg_list:
                colors.append('g')
            elif node in shortest_path:
                colors.append('b')
            else:
                colors.append('r')
        #colors = node_colors(G, shortest_path, mg_list)

        nx.draw_networkx_edges(G, pos, width=3, alpha=0.5, edge_color='r')
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=280)
        nx.draw_networkx_edges(G, pos, edgelist=shortest_edges, edge_color='b', width=3)
        #nx.draw_networkx_labels(G, pos, font_size=12, font_family='sans-serif')
        #nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_cost)

        nnode = mpatches.Circle((0.3, 0.3), 0.2, facecolor="red", edgecolor="red", linewidth=1)
        bnode = mpatches.Circle((0.3, 0.3), 0.2, facecolor="blue", edgecolor="blue", linewidth=1)
        gnode = mpatches.Circle((0.3, 0.3), 0.2, facecolor="green", edgecolor="red", linewidth=1)
        # plt.gca().add_patch(c)

        plt.legend([nnode, bnode, gnode], ['Normal Node', 'Shortest Path Node', 'Migrated Node'],
                   handler_map={mpatches.Circle: HandlerCircle()})
        plt.axis('off')
        plt.plot()
        plt.show()
        # ends here if any error

    def plot_ANFIS_status(self ,G, rp_list=[], ug_list=[]):
        pos = nx.spring_layout(G)  # positions for all nodes

        colors = []
        for node in G.nodes():
            if node in ug_list:
                colors.append('g')
            elif node in rp_list:
                colors.append('r')
            else:
                colors.append('b')
        #colors = node_colors(G, shortest_path, mg_list)

        nx.draw_networkx_edges(G, pos, width=3, alpha=0.5, edge_color='b')
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=300)


        nnode = mpatches.Circle((0.3, 0.3), 0.2, facecolor="blue", edgecolor="red", linewidth=1)
        bnode = mpatches.Circle((0.3, 0.3), 0.2, facecolor="red", edgecolor="blue", linewidth=1)
        gnode = mpatches.Circle((0.3, 0.3), 0.2, facecolor="green", edgecolor="red", linewidth=1)
        # plt.gca().add_patch(c)

        plt.legend([nnode, bnode, gnode], ['Un-classified','Classified: Replace', 'Classified: Upgrade'],
                   handler_map={mpatches.Circle: HandlerCircle()})
        plt.axis('off')
        plt.plot()
        plt.show()
        # ends here if any error


    def view_networkx_graph(self,G,g):
        pos = nx.spring_layout(G)  # positions for all nodes

        colors = []
        mglist = g.get_migrated_list()
        for node in G.nodes():
            if node in mglist:
                colors.append('g')
            else:
                colors.append('r')

        plt.subplot(1, 1, 1)
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=300)
        # edges
        nx.draw_networkx_edges(G, pos, width=3, alpha=0.5, edge_color='r')
        nx.draw_networkx_labels(G, pos, font_size=8, font_family='sans-serif')
        edge_cost = nx.get_edge_attributes(G, 'weight')
        #nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_cost)
        # labels
        plt.axis('off')
        plt.title('Migration Topology Graph')
        plt.plot()
        plt.show()


    def shared_cost_coeff(self):
        def t(mu, k):
            return pow(1 / mu, k)  # k is the corelation coefficient between SDN and IPv6

        mu = np.arange(1, 2.1, 0.1)  # cost sharing factor between SDN and IPv6
        #plt.subplot(1, 2, 1)
        plt.plot(mu, t(mu, 0.0), '-or', label='$\epsilon$=0.0')
        plt.plot(mu, t(mu, 0.2), '-oc', label='$\epsilon$=0.2')
        plt.plot(mu, t(mu, 0.4), '-pg', label='$\epsilon$=0.4')
        plt.plot(mu, t(mu, 0.6), '-<y', label='$\epsilon$=0.6')
        plt.plot(mu, t(mu, 0.8), '->k', label='$\epsilon$=0.8')
        plt.plot(mu, t(mu, 1.0), '-vb', label='$\epsilon$=1.0')
        plt.xlabel(r'Shared cost coefficient ($\mu$)')
        plt.ylabel(r'Migration cost variance ($T^i_s$)')
        plt.legend()
        plt.grid(True)
        plt.show()

        # # for percentage optimized based on shared cost coefficeint and strength of correlation
        # def percent_optimize(epsala, mu):
        #     return (1-pow(1/mu,epsala))*100          #measured in percentage
        #
        # epsala = np.arange(0, 1.02, 0.2)
        # mu = 2
        # #plt.subplot(1, 2, 2)
        # plt.plot(epsala, percent_optimize(epsala, mu), '-or')
        # plt.xlabel(r'Strength of correlation ($\epsilon$)')
        # plt.ylabel(r'percentage of total joint migraiton cost optimization')
        # plt.legend()
        # plt.grid(True)
        # plt.show()



        """
        #this plot is for IEEE CIC paper of migrant routers cost optimziation
        def t1(no, mu, k):
            return no * pow(1 / mu, k)

        
        mu = 2
        no = np.arange(50, 501, 50)
        plt.subplot(1, 2, 2)
        plt.plot(no, t1(no, mu, 0.0), '-or', label='$\epsilon$=0.0')
        plt.plot(no, t1(no, mu, 0.2), '-oc', label='$\epsilon$=0.2')
        plt.plot(no, t1(no, mu, 0.4), '-pg', label='$\epsilon$=0.4')
        plt.plot(no, t1(no, mu, 0.6), '-<y', label='$\epsilon$=0.6')
        plt.plot(no, t1(no, mu, 0.8), '->k', label='$\epsilon$=0.8')
        plt.plot(no, t1(no, mu, 1.0), '-vb', label='$\epsilon$=1.0')
        plt.xlabel('Number of Migrant Routers at $\mu$=1.5')
        plt.ylabel(r'Migration cost variance (multiple of $1500)')
        plt.legend()
        plt.grid(True)
        plt.show()
        """
    def energy_plot(self):
        plot_switch = pd.read_csv('switch_plot.csv')
        plot_links = pd.read_csv('links_plot.csv')
        img_switch = pimg.imread('./EnergySwitch.jpg')
        img_links = pimg.imread('./EnergyLinks.jpg')

        plt.subplot(2,2,1)
        plt.plot(plot_switch['switch_no'], plot_switch['old_system'])
        plt.plot(plot_switch['switch_no'], plot_switch['new_system'])
        plt.title('Energy consumption ratio')
        plt.xlabel('Number of Switches')
        plt.ylabel('Energy Consumption per Year (MWh)')
        plt.legend(['Energy consumption by legacy system', 'Energy consumption by SoDIP6 network'])

        plt.subplot(2, 2, 2)
        plt.plot(plot_links['switch_no'], plot_links['old_system'])
        plt.plot(plot_links['switch_no'], plot_links['new_system'])
        plt.title('Energy consumption ratio')
        plt.xlabel('Number of Links')
        plt.ylabel('Energy Consumption per Year (MWh)')
        plt.legend(['Energy consumption by legacy system', 'Energy consumption by SoDIP6 network'])

        plt.subplot(2, 2, 3)
        plt.imshow(img_switch)
        plt.subplot(2, 2, 4)
        plt.imshow(img_links)

        plt.show()
        #it has wrong plot please avoid
        # plot_switch_power = pd.read_csv('../RuralSoDIP6/recSwitchTotPowerGraph.csv')
        # plot_links_power = pd.read_csv('../RuralSoDIP6/recLinkPower.csv')
        # x=[]
        # y=[]
        # z=[]
        # with open('../RuralSoDIP6/recSwitchTotPowerGraph.csv','r') as csvfile:
        #     data = csv.reader(csvfile,delimiter=',')
        #     for col in data:
        #         x.append(col[0])
        #         y.append(col[1])
        #         z.append(col[2])
        #
        # plt.subplot(2,1,1)
        # plt.plot(x,y,'-or',label='SoDIP6')
        # plt.plot(x,z, '-pg',label='Legacy IPv4')
        # plt.title('Energy consumptions by switches')
        # plt.xlabel('time step')
        # plt.ylabel('Energy Consumption (Wh)')
        # plt.legend()
        #
        # plt.subplot(2, 1, 2)
        # plt.plot(plot_links_power['Time'], plot_links_power['SoDIP6'])
        # plt.plot(plot_links_power['Time'], plot_links_power['Old'])
        # plt.title('Energy consumptions by links')
        # plt.xlabel('time step')
        # plt.ylabel('Energy Consumption (Wh)')
        # plt.legend()
        # plt.show()

    def graph_joint_budget(self):
        phase_r = np.arange(1, 4, 1)
        budget_r = [6, 3, 3]

        phase_a = np.arange(1, 6, 1)
        budget_a = [4.5, 3, 1.5, 4.5, 3]

        phase_x = np.arange(1, 15, 1)
        budget_x = [4.5, 4.5, 4.5, 3, 1.5, 1.5, 4.5, 1.5, 1.5, 3, 1.5, 1.5, 1.5, 1.5]

        bar_width = 0.25
        fig, ax = plt.subplots()
        reacts1 = plt.bar(phase_r, budget_r, bar_width, alpha=0.8, color='r', label='Random Network(8 nodes, 13 links)')
        reacts2 = plt.bar(phase_a + bar_width, budget_a, bar_width, alpha=0.7, color='b',
                          label='Abilene Network(11 nodes, 14 links)')
        reacts3 = plt.bar(phase_x + 2 * bar_width, budget_x, bar_width, alpha=0.6, color='g',
                          label='Xeex Network(24 nodes, 34 links)')
        plt.xticks(phase_x + 1.6 * bar_width, (
            '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th', '13th', '14th'))

        plt.tight_layout()
        plt.xlabel('Priority migration phase based on shortest path', fontsize=15)
        plt.ylabel('Phase wise priority migration cost (multiple of $1500)', fontsize=15)
        plt.legend()
        plt.show()

    def utility_game_theory(self):
        #this section is not used the final plot were taken from 1st, 2nd and 3rd round of game theory
        timestep=np.arange(24)
        N=1200
        custlist33 =[]
        custlist53 =[]
        custlist55 =[]
        custlist22 =[]

        custlist33.append(N)
        custlist53.append(N)
        custlist55.append(N)
        custlist22.append(N)

        valList33 =[]
        valList53 =[]
        valList55 =[]
        valList22 =[]

        demand_33=0
        demand_53=0
        demand_55=0
        demand_22=0

        for i in timestep:
            demand_33 +=round(int(custlist33[i])*0.01)
            demand_53 +=round(int(custlist33[i])*0.03)
            demand_55 += round(int(custlist55[i]) * 0.05)
            demand_22 += round(int(custlist22[i]) * 0.005)

            next_cust33=round(int(custlist33[i])*0.98)
            next_cust53=round(int(custlist53[i])*0.97)
            next_cust55=round(int(custlist55[i])*0.95)
            next_cust22=round(int(custlist22[i])*1.02)

            sigma_c33 = demand_33/custlist33[i]*np.exp((custlist33[i]-next_cust33)/custlist33[i])
            sigma_c53 = demand_53 / custlist53[i] * np.exp((custlist53[i] - next_cust53) / custlist53[i])
            sigma_c55 = demand_55 / custlist55[i] * np.exp((custlist55[i] - next_cust55) / custlist55[i])
            sigma_c22 = demand_22 / custlist22[i] * np.exp((custlist22[i] - next_cust22) / custlist22[i])

            valList33.append(sigma_c33)
            valList53.append(sigma_c53)
            valList55.append(sigma_c55)
            valList22.append(sigma_c22)

            custlist33.append(next_cust33)
            custlist53.append(next_cust53)
            custlist55.append(next_cust55)
            custlist22.append(next_cust22)

        custlist33.pop()
        custlist53.pop()
        custlist55.pop()
        custlist22.pop()

        plt.subplot(2, 3, 1)
        plt.plot(timestep, valList33, '-or', label='$\sigma_c$ at (1%$\u2191$,-2%$\u2193$)')
        plt.plot(timestep, valList53, '-pg', label='$\sigma_c$ at (3%$\u2191$,-3%$\u2193$)')
        plt.plot(timestep, valList55, '->k', label='$\sigma_c$ at (5%$\u2191$,-5%$\u2193$)')
        plt.plot(timestep, valList22, '-vb', label='$\sigma_c$ at (0.5%$\u2191$, 2%$\u2191$)')
        plt.xlabel('Number of Time Steps\n(a)')
        plt.ylabel(ylabel='$\sigma_c$')
        plt.xlim(-1,25)
        plt.legend()
        plt.grid(True)

        ipv6in=300
        ipv4in=900
        npall=16
        np4=npall
        traffic25=[]
        for i in timestep:
            ipv6in+=ipv6in*0.02     #ipv6 traffic increament by 2%
            ipv4in+=ipv4in*0.05     #ipv4 traffic increment by 5%
            traf_status= (npall-np4)/npall*ipv6in/(ipv4in+ipv6in)
            np4-=npall/24
            traffic25.append(traf_status)

        plt.subplot(2, 3, 2)
        plt.plot(timestep, traffic25, '-pg', label='$\sigma_p$ at (2%$\u2191$,5%$\u2191$)')

        ipv6in=300
        ipv4in=900
        npall=16
        np4=npall
        traffic55=[]
        for i in timestep:
            ipv6in+=ipv6in*0.05     #ipv6 traffic increament by 2%
            ipv4in-=ipv4in*0.02     #ipv4 traffic increment by 0.5%%
            traf_status= (npall-np4)/npall*ipv6in/(ipv4in+ipv6in)
            np4-=npall/24
            traffic55.append(traf_status)

        plt.plot(timestep, traffic55, '-or', label='$\sigma_p$ at (5%$\u2191$,-2%$\u2193$)')

        ipv6in=300
        ipv4in=900
        npall=16
        np4=npall
        traffic12=[]
        for i in timestep:
            ipv6in+=ipv6in*0.10     #ipv6 traffic increament by 2%
            ipv4in-=ipv4in*0.02     #ipv4 traffic increment by 0.8%%
            traf_status= (npall-np4)/npall*ipv6in/(ipv4in+ipv6in)
            np4-=npall/24
            traffic12.append(traf_status)

        plt.plot(timestep, traffic12, '->k', label='$\sigma_p$ at (10%$\u2191$,-2%$\u2193$)')
        plt.xlim(-1,25)
        plt.xlabel('Number of Time Steps\n(b)')
        plt.ylabel(ylabel='$\sigma_p$')
        plt.legend()
        plt.grid(True)

        hrall=120
        hrs6=2
        bt=30
        cm=45

        hrval22=[]
        for hr6 in timestep:
            bt+=bt*0.02
            cm+=cm*0.002
            hrs6+=hrs6/24
            valhr=hr6*bt/(hrall*cm)
            hrval22.append(valhr)

        plt.subplot(2, 3, 3)
        plt.plot(timestep, hrval22, '-pg', label='$\sigma_s$ at(2%$\u2191$,0.2%$\u2191$)')

        hrs6=2
        bt=30
        cm=45
        hrval52=[]
        for hr6 in timestep:
            bt+=bt*0.05
            cm+=cm*0.002
            hrs6+=hrs6/24
            valhr=hr6*bt/(hrall*cm)
            hrval52.append(valhr)

        plt.plot(timestep, hrval52, '-vb', label='$\sigma_s$ at (5%$\u2191$,0.2%$\u2191$)')
        plt.xlabel('Number of Time Steps\n(c)')
        plt.ylabel(ylabel='$\sigma_s$')
        plt.xlim(-1,25)
        plt.legend()
        plt.grid(True)
#        plt.show()

        sigma32=[]
        sigma53=[]
        for i in range(24):
            sigma32.append(valList22[i]+traffic25[i]+hrval22[i])
            sigma53.append(valList53[i]+traffic55[i]+hrval52[i])

        plt.subplot(2,3,4)
        plt.plot(timestep, sigma32, '-ob',
                 label='$\sigma$ at $\sigma_c$(0.5%$\u2191$,2%$\u2191$), $\sigma_p$(2%$\u2191$,5%$\u2191$) & $\sigma_s$(2%$\u2191$,0.2%$\u2191$)')
        plt.plot(timestep, sigma53, '-pg',
                 label='$\sigma$ at $\sigma_c$(3%$\u2191$,-3%$\u2193$),$\sigma_p$(5%$\u2191$,-2%$\u2193$) & $\sigma_s$(5%$\u2191$,0.2%$\u2191$)')
        plt.xlabel('Number of Time Steps')
        plt.xlim(-1,25)
        plt.legend()
        plt.grid(True)
        #plt.show()

        # graphs of ISP utilities simulation of evolutionary dynamics
        def v4_utility(x46, N1):
            return np.log(1 + (N1 - x46) * 500)  # k is the corelation coefficient between SDN and IPv6

        def v6_utility(x46, N2):
            return np.log(1 + (N2 + x46) * 700)

        N = 16
        N1 = N / 2
        N2 = N - N1
        x46 = np.arange(0, N1 + 0.001, 1)  # cost sharing factor between SDN and IPv6
        plt.subplot(2, 3, 5)
        plt.plot(x46, v4_utility(x46, N1), '-or', label='Group-1(initially 8 legacy IPv4 ISPs)')
        plt.plot(x46, v6_utility(x46, N2), '-pg', label='Group-2(initially 8 SoDIP6 ISPs)')
        plt.xlabel('(a) X4->6 (Number of SoDIP6 ISPs)')
        plt.ylabel('U$_k$')
        plt.legend()
        plt.grid(True)

        N1 = 12
        N2 = N - N1
        x46 = np.arange(0, N1 + 0.001, 1)
        plt.subplot(2, 3, 6)
        plt.plot(x46, v4_utility(x46, N1), '-or', label='Group-1(Initially 12 Legacy IPv4 ISPs)')
        plt.plot(x46, v6_utility(x46, N2), '-pg', label='Group-2(Initially 4 SoDIP6 ISPs)')
        plt.xlabel('(b) X4->6 (Number of SoDIP6 ISPs)')
        plt.ylabel('U$_k$')
        plt.legend()
        plt.grid(True)
        plt.show()

    def simulation_plot(self,mg_no_list, mg_cost_list):
        sp_phase = np.arange(1, len(mg_no_list)+1, 1)  # cost sharing factor between SDN and IPv6
        bar_width = 0.25
        plt.subplot(1, 2, 1)
        rect = plt.bar(sp_phase, mg_no_list, bar_width, alpha=0.8, color='b', label='Un-migrated Routers')
        plt.xlabel('(a) Migration Phases - shortest path')
        plt.ylabel('No of unmigrated routers per phase shortest path')
        plt.legend()
        for v in rect:
            height = v.get_height()
            plt.text(v.get_x() + v.get_width() / 2., height,'%d' % int(height),ha='center', va='bottom')
        #plt.grid(True)

        def t1(no, mu, k):
            return no * np.power(1/mu,k)

        mu = 2
        s = pd.Series(mg_cost_list)
        plt.subplot(1, 2, 2)
        #plt.plot(sp_phase, s/1000, '-or', label='non optimized cost') #non optimized cost plot
        bar_width=0.12
        sp_phase1=[x+bar_width for x in sp_phase]
        sp_phase2=[x+bar_width for x in sp_phase1]
        sp_phase3=[x+bar_width for x in sp_phase2]
        sp_phase4 = [x + bar_width for x in sp_phase3]

        plt.bar(sp_phase, s*pow(1/mu,0.0)/1000,bar_width, alpha=0.8, color='b', label='$\epsilon$=0.0, 0% optimized')
        plt.plot(sp_phase, s * pow(1 / mu, 0.0) / 1000, '-ob')
        plt.bar(sp_phase1, s*pow(1/mu,.4)/1000, bar_width, alpha=0.8, color='r',label='$\epsilon$=0.4, 24.21% optimized')
        plt.bar(sp_phase2, s*pow(1/mu,.6)/1000, bar_width, alpha=0.8, color='g',label='$\epsilon$=0.6, 34.02% optimized')
        plt.bar(sp_phase3, s*pow(1/mu,.8)/1000, bar_width, alpha=0.8, color='y',label='$\epsilon$=0.8, 42.56% optimized')
        plt.plot(sp_phase, s * pow(1 / mu, .8) / 1000, '-<y', label='$\epsilon$=0.8, 42.56% optimized')
        plt.bar(sp_phase4, s*pow(1/mu,1.0)/1000, bar_width, alpha=0.8, color='k', label='$\epsilon$=1.0, 50% optimized')
        plt.xlabel('(b) Migration phases - shortest path', fontweight='bold')
        plt.ylabel(r'Joint Migration cost per phase shortest path (Multiple of $1000)')
        plt.xticks([x + bar_width for x in range(len(sp_phase)+1)], [' ', '1st', '2nd', '3rd', '4th', '5th',
                                                '6th', '7th', '8th', '9th', '10th', '11th', '12th', '13th', '14th'])
        plt.legend()
        plt.show()

#from control placement functions

    def plot_with_controller(self,G,g):
        pos = nx.spring_layout(G)  # positions for all nodes

        colors = []
        #mglist = g.get_migrated_list()
        for node in G.nodes():
            if g.get_router(node).type is 'R':
                colors.append('m')
            elif g.get_router(node).type is 'S':
                colors.append('g')
            elif g.get_router(node).type is 'SG':
                colors.append('c')
            elif g.get_router(node).type is 'ASG':
                colors.append('k')
            else:
                colors.append('b')

        plt.subplot(1, 1, 1)
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=300)
        # edges
        nx.draw_networkx_edges(G, pos, width=3, alpha=0.5, edge_color='r')
        nx.draw_networkx_labels(G, pos, font_size=8, font_family='sans-serif')
        #edge_cost = nx.get_edge_attributes(G, 'weight')
        #nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_cost)
        # labels
        plt.axis('off')
        plt.title('Graphs with ONOS/SDDIP Controller')
        plt.show()

    def plot_latency_sp(self, switch_latency_list, gateway_latency_list):
        switchx, switchy = map(list, zip(*switch_latency_list))
        plt.subplot(121)
        plt.plot(switchy,'-ob', label='SDN swtich latency')
        plt.xticks([x for x in range(len(switchx))],switchx)
        plt.xlabel('Qumulative number of switches migrated', fontweight='bold')
        plt.ylabel('Control path latency by SDN switch')
        plt.grid(True)

        #for gateway
        plt.subplot(122)
        gatex, gatey = map(list, zip(*gateway_latency_list))
        plt.plot(gatey, '->r', label='switch gateway latency')
        plt.xticks([x for x in range(len(gatex))], gatex)
        plt.xlabel('Number of BGP-peers formed in incremental router migration', fontweight='bold')
        plt.ylabel('Control path latency by BGP Peers')
        plt.grid(True)
        plt.show()
        return

    # def plot_latency_gateway(self, gateway_latency_list):
    #     gatex, gatey = map(list, zip(*gateway_latency_list))
    #     plt.plot(gatey, '->r', label='switch gateway latency')
    #     plt.xticks([x for x in range(len(gatex))],gatex)
    #     plt.xlabel('No of switch gateway', fontweight='bold')
    #     plt.ylabel('Gateway latency')
    #     plt.show()
    #     return



