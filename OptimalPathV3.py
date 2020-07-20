from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import traceback
import random
from tqdm import tqdm
from collections import defaultdict, deque
import PIL.Image, PIL.ImageTk
from collections import OrderedDict
from sodip6.graphs import *
from sodip6.customers import *
from sodip6.implementANFIS import *
from sodip6.controllerPlacement import *
import matplotlib
font = {'family': 'Times new roman',
         'size' : 14}
matplotlib.rc('font', **font)

G,g,C,pr_router=None,None,None,None


class Router:
    def __init__(self, node):
        self.id = node
        self.adjacent = {}

        # set initial snmp parameter information, load randomely from json dictionary
        self.set_snmp_param()

    def add_neighbor(self, neighbor, weight=0):
        self.adjacent[neighbor] = weight

    def get_neighbors(self):
        return self.adjacent

    def get_connections(self):
        return self.adjacent.keys()

    def get_id(self):
        return self.id

    def get_weight(self, neighbor):
        return self.adjacent[neighbor]

    def get_ipv6_status(self):
        return self.ipv6_enable

    def get_openflow_status(self):
        return self.openflow_enable

    def set_migration(self, SoDIP6):
        self.ipv6_enable = SoDIP6
        self.openflow_enable = SoDIP6

    def get_migration(self):
        if self.ipv6_enable == True and self.openflow_enable == True:
            return True
        else:
            return False

    def get_replace_upgrade(self):
        #self.replace_upgrade = ANFIS_Device.get_device_status(self) # enable after perfect coding
        return self.replace_upgrade #get_anfis_status(self.device_no)

    def get_cpu_usage(self):
        return round(random.uniform(25, 90),2)

    def get_memory_usage(self):
        return random.randint(4, int(self.mem_size))

    def get_memory_unused(self):
        return int(self.mem_size)-self.get_memory_usage()+random.randrange(16,1024,16)

    def get_throughput(self):
        return random.randint(10,2048) #throughput in mbps

    def set_type(self,type):
        self.type=type

    def get_type(self):
        return self.type

    # This function initialize the snmp parameters for each routers
    def set_snmp_param(self):
        # retrieve all paramters from the random generation from file location and put into thread to count the up time
        with open('initialSoDIP6.json') as json_file:
            device_details = json.load(json_file)
            device_count = len(device_details)
            self.device_no = 'Device_' + str(random.sample(range(device_count), 1).pop())

            self.ios_name = device_details[self.device_no]["ios_name"]
            self.ios_version = device_details[self.device_no]["ios_version"]
            self.device_id = device_details[self.device_no]["device_id"]
            self.up_time = device_details[self.device_no]["up_time"]
            self.cpu_speed = device_details[self.device_no]["cpu_speed"]
            self.mem_size = device_details[self.device_no]["mem_size"]
            self.ipv6_enable = device_details[self.device_no]["ipv6_enable"]
            self.openflow_enable = device_details[self.device_no]["openflow_enable"]
            self.replace_upgrade = device_details[self.device_no]["replace_upgrade"]
            json_file.close()
            self.cpu_usage = self.get_cpu_usage()
            self.memory_usage = self.get_memory_usage()
            self.throughput = self.get_throughput()
            self.type = "R" #S, SG, ASG, BGPS, RSS
            #R -> leagacy router, S -> SDN switch, SG -> switch gatenway, ASG -> AS Gateway, BGPS -> BGP speaker,\
            #RSS -> root soure switch

    # This function extracts the realtime router details to analyze its facts to identiy its status
    def get_snmp_details(self):
        dev_no = self.device_no
        dev_details = {}
        dev_details[dev_no] = {}
        dev_details[dev_no]['ios_name'] = self.ios_name
        dev_details[dev_no]['device_id'] = self.device_id
        dev_details[dev_no]['up_time'] = self.up_time
        dev_details[dev_no]['cpu_speed'] = self.cpu_speed
        dev_details[dev_no]['mem_size'] = self.mem_size
        dev_details[dev_no]['ipv6_enable'] = self.ipv6_enable
        dev_details[dev_no]['openflow_enable'] = self.openflow_enable
        dev_details[dev_no]['replace_upgrade'] = self.replace_upgrade
        return dev_details

    def get_migration_cost(self):
        ios_upgrade_cost = 275.0
        hw_upgrade_cost = 700.0
        replacement_cost = 7000.0
        support_cost = 140.0
        hr_dev_cost = 250.0
        misc_cost = 75.0
        migration_cost = support_cost+hr_dev_cost+misc_cost
        migration_cost += replacement_cost if self.replace_upgrade == "R" else ios_upgrade_cost + hw_upgrade_cost
        return migration_cost


class TopoSoDIP6:  # This class creates the graphs of routers and links
    def __init__(self):
        self.edges = defaultdict(list)
        self.distances = {}

        self.vert_dict = {}  # put all the routers into dictionary
        self.num_vertices = 0  # count number of routers in the topology

    def add_router(self, node):
        self.num_vertices = self.num_vertices + 1
        new_router = Router(node)
        self.vert_dict[node] = new_router
        return new_router

    def get_router(self, n):
        if n in self.vert_dict:
            return self.vert_dict[n]
        else:
            return None

    def add_edge(self, frm, to, weight=0.0):
        if frm not in self.vert_dict:
            self.add_router(frm)
        if to not in self.vert_dict:
            self.add_router(to)

        self.edges[frm].append(to)
        self.edges[to].append(frm)
        self.distances[(frm, to)] = weight
        self.distances[(to, frm)] = weight

        self.vert_dict[frm].add_neighbor(self.vert_dict[to], weight)
        self.vert_dict[to].add_neighbor(self.vert_dict[frm], weight)

    def get_vertices(self):
        return self.vert_dict.keys()

    def get_migrated_list(self):
        migrated_list = []
        for node in self.vert_dict.keys():
            if (self.vert_dict[node]).get_migration() is True:
                migrated_list.append(node)
        return migrated_list


    def get_legacy_list(self):
        legacy_list = []
        for node in self.vert_dict.keys():
            if (self.vert_dict[node]).get_migration() is False:
                legacy_list.append(node)
        return legacy_list

    #below functions are for ONOS/SDNIP implementation
    def get_switch_list(self):
        switch_list = []
        for node in self.vert_dict.keys():
            if (self.vert_dict[node]).get_type() is 'S':
                switch_list.append(node)
        return switch_list

    def get_switch_gateways(self):
        switch_gateways = []
        for node in self.vert_dict.keys():
            if (self.vert_dict[node]).get_type() is 'SG':
                switch_gateways.append(node)
        return switch_gateways

    def get_external_gateways(self):
        external_gateways = []
        for node in self.vert_dict.keys():
            if (self.vert_dict[node]).get_type() is 'ASG':
                external_gateways.append(node)
        return external_gateways

#onlye call this funcition at the last to perform migration of stub routers/SG
    def get_routers_list(self):
        rtrs = []
        for node in self.vert_dict.keys():
            if (self.vert_dict[node]).get_type() in ['R','SG']:
                rtrs.append(node)
        return rtrs


def optimal_path(g, origin, destination):
    if origin == destination:
        return None,None
    def shortest(g, initial):
        visited = {initial: 0}
        path = {}

        # nodes = set(g.nodes)
        nodes = set(g.vert_dict.keys())
        while nodes:
            min_node = None
            for node in nodes:
                if node in visited:
                    if min_node is None:
                        min_node = node
                    elif visited[node] < visited[min_node]:
                        min_node = node
            if min_node is None:
                break

            nodes.remove(min_node)
            current_weight = visited[min_node]

            for edge in g.edges[min_node]:
                try:
                    weight = current_weight + g.distances[(min_node, edge)]
                except:
                    continue
                if edge not in visited or weight < visited[edge]:
                    visited[edge] = weight
                    path[edge] = min_node

        return visited, path

    visited, paths = shortest(g, origin)
    full_path = deque()
    _destination = paths[destination]

    while _destination != origin:
        full_path.appendleft(_destination)
        _destination = paths[_destination]

    full_path.appendleft(origin)
    full_path.append(destination)

    return visited[destination], list(full_path)


def print_graph_details(g):
    for v in g:
        for w in v.get_connections():
            vid = v.get_id()
            wid = w.get_id()
            wt = v.get_weight(w)
            ios_name = w.device_id
            print('( %s , %s, weight=%.2f, id=%s)' % (vid, wid, wt, ios_name))
            # G.add_edge(str(vid),str(wid),weight=float(wt))


class ResizingCanvas(Canvas):
    def __init__(self,parent,**kwargs):
        Canvas.__init__(self,parent,**kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_width()

    def on_resize(self,event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.scale("all",0,0,wscale,hscale)

def main():
    global G
    global g
    global C
    global pr_router

    # bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)
    # for i in range(20):
    #     time.sleep(0.1)
    #     bar.update(i)

    root = Tk()
    G = nx.Graph()
    g = TopoSoDIP6()
    C = CustomerDetails()
    plotme = PlotGraphs()
    menubar = Menu(root)

    def open_topology():
        global G
        global g
        file_open = filedialog.askopenfilename(initialdir='D:\PhD-Study\Experimental\SoDIP6', title='Select file', \
                    filetypes=(('GML files', '*.gml'),('CSV files', '*.csv'), ('All files', '*.*')))
        text_display.insert(END,"\nLoading Network Graphs..........",'a')
        if file_open.endswith('.gml'):
            try:
                G = nx.read_gml(file_open)
                for u, v, w in G.edges(data=True):
                    g.add_edge(u, v, weight=float(w['weight']))  # if w['LinkType'] == 'OC-192' else 100.0)
            except FileNotFoundError:
                print('File not found')
            #except KeyError:
            #    nx.set_edge_attributes(G, 10.0, name='weight')
        elif file_open.endswith('.csv'):
            G = nx.Graph()
            try:
                with open(file_open) as graph_file:
                    read_file = csv.DictReader(graph_file)
                    for row in read_file:
                        g.add_edge(row['node_from'], row['node_to'], weight=float(row['bandwidth']))
                        G.add_edge(row['node_from'], row['node_to'], weight=float(row['bandwidth']))
            except FileNotFoundError:
                print('File or node error')
        else:
            messagebox.showerror('SoDIP6','Could Not Load file')
            return
        text_display.insert(END,"\nGraph Successfully Loaded....",'a')
        total_nodes = G.nodes()
        text_display.insert(END,"\nTotal nodes are:"+str(len(total_nodes))+"\n Nodes are:"+str(total_nodes),'a')

        '''#generate CSF from GML
        try:
            with open('./dataset/generate_csv.csv', 'w', newline='') as write_csv:
                writer = csv.writer(write_csv)
                writer.writerow(['id','Name', 'Latitude', 'Longitude'])
                id=0
                for node, attrs in list(G.nodes(data=True)):
                    writer.writerow([id,str(node),attrs['Longitude'],attrs['Latitude']])
                    id+=1
        finally:
            write_csv.close()
        '''
    filemenu = Menu(menubar, tearoff=1)
    filemenu.add_command(label="Open", command=open_topology)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=lambda: quit())
    menubar.add_cascade(label="File", menu=filemenu)
    networkmenu = Menu(menubar, tearoff=1)

    def print_graph_details():
        #text_display.delete(1.0,END)
        global G
        global g
        try:
            text_display.delete('1.0', END)
            strtxt = 'Total number of nodes:'+ str(G.number_of_nodes())
            text_display.insert(END,strtxt+'\n','a')
            strtxt = 'Total number of edges:'+ str(G.number_of_edges())
            text_display.insert(END,strtxt+'\n','a')
            strtxt = 'List of Migrated Node:' + str(g.get_migrated_list())+', ' \
                                            '\nTotal Migrated:'+ str(len(g.get_migrated_list()))
            text_display.insert(END,strtxt+'\n','a')
            strtxt = 'List of Legacy Nodes:' + str(g.get_legacy_list())
            text_display.insert(END,strtxt+'\n','a')
        except NameError:
            messagebox.showerror("SoDIP6", "Please Load Network Topology First")
            return

    def locate_controller():
        # get the graph and dictionaries of shortest path
        global g, pr_router
        fg_router = ghrentry.get()
        if fg_router not in g.vert_dict.keys():
            messagebox.showerror("SoDIP6", "Foreign gateway router not recognized...")
            return
        g.get_router(fg_router).set_type(type='ASG')
        pr_router.remove(fg_router)
        sp_list = [[] for _ in range(len(pr_router))]
        for i in range(len(pr_router)):
            path_cost, sp_list[i] = optimal_path(g, pr_router[i], fg_router)
        valid_list = list(filter(None, sp_list))  # [lst for lst in sp_list if lst]
        valid_list.sort(key=len, reverse=True)
        median_router = valid_list[0][math.ceil((len(valid_list[0]) * 2 / 4)) - 1]
        rss_left = valid_list[0][math.ceil((len(valid_list[0]) * 1 / 4)) - 1]
        rss_right = valid_list[0][math.ceil((len(valid_list[0]) * 3 / 4)) - 1]
        rss = median_router
        set_migration_as(G, g, valid_list, rss)
        #text_display.delete('1.0', END)
        # text_display.insert(END,"\nSuitable master controller switch is:"+rss)
        # text_display.insert(END,"\n East bound controller shall be: "+rss_right)
        # text_display.insert(END,"\n West bound controller shall be: "+rss_left)

    def plot_shortest_path():
        # fhr: firts hop router in the network as a source in the ISP edge or at customer premises
        global g
        st_path = None
        path_cost = None
        for nv in g.vert_dict.keys():
            (g.vert_dict[nv]).visited = False

        text_display.delete('1.0', END)
        fhr, ghr = fhrentry.get(),ghrentry.get()
        if fhr not in g.vert_dict.keys() or ghr not in g.vert_dict.keys():
            messagebox.showerror("SoDIP6", "Shortest path router not recognized")
            return
        try:
            path_cost, st_path = optimal_path(g, fhr, ghr)  # implements dijkstra's shortest path algorithm
        except NameError:
            messagebox.showerror("SoDIP6", "Please Load Network Topology First")
        # print(find_all_paths(G, fhr, ghr))
        strtxt = 'Shortest Path: '+str(st_path)
        text_display.insert(END,strtxt,'a')

        if st_path is None:
            text_display.insert(END,"\nCan't plot graph-error...")
            return
        for rnode in st_path:
            strtxt = '\nRouter '+ rnode +' Migration to SoDIP6:' + str((g.get_router(rnode)).get_migration())
            text_display.insert(END,strtxt,'a')

        strtxt = '\nThe Shortest Edge Cost :'+ str(path_cost)
        text_display.insert(END,strtxt,'a')

        shortest_edges = []
        length = len(st_path)
        for x in range(0, length - 1):
            shortest_edges.append((st_path[x], st_path[x + 1]))
        # path = nx.shortest_path(G, fhr, ghr, weight='weight')
        strtxt = '\nEdges in the shortest path:' + str(shortest_edges)
        text_display.insert(END, strtxt, 'a')
        mg_list = [mg_node for mg_node in g.vert_dict.keys() if (g.get_router(mg_node)).get_migration() is True]
        #graph view at the plot
        plotme.plot_graph(G, st_path, shortest_edges, mg_list)

    def migrate_shortest_path():
        global g

        fhr,ghr=fhrentry.get(),ghrentry.get()

        if fhr not in g.vert_dict.keys() or ghr not in g.vert_dict.keys():
            messagebox.showerror("SoDIP6", "Shortest path router not recognized")
            return
        text_display.delete('1.0',END)
        path_cost, shortest_path = optimal_path(g, fhr, ghr)  # implements dijkstra's shortest path algorithm
        strtxt = 'Shortest path from '+ fhr +' to '+ ghr +' is: '+ str(shortest_path)
        text_display.insert(END,strtxt,'a')
        shortest_edges = []
        length = len(shortest_path)
        for x in range(0, length - 1):
            shortest_edges.append((shortest_path[x], shortest_path[x + 1]))

        try:
            unmigrated_nodes = [v for v in shortest_path if (g.get_router(v)).get_migration() is False]
            yesno = False
            if len(unmigrated_nodes) == 0:
                messagebox.showinfo("SoDIP6", "All legacy nodes on this paths are migrated")
                return
            else:
                migration_cost = 0.0
                for rnode in unmigrated_nodes:
                    migration_cost += (g.get_router(rnode)).get_migration_cost()
                yesno = messagebox.askokcancel("SoDIP6", "Legacy nodes to migrates are:"+ str(unmigrated_nodes)+"\n"
                                                "Total migration cost: " + str(migration_cost)+"\n"
                                                "Do you want to migrate all?", icon='warning')
            if yesno is True:
                for rnode in unmigrated_nodes:
                    (g.get_router(rnode)).set_migration(True)
                messagebox.showinfo("SoDIP6","Migrated Successfully")
                print_graph_details()
            else:
                return
        except:
            traceback.print_exc()

    def add_new_customer():
        global C
        global g
        cust_win = Tk()
        cust_win.wm_title("Add New Customer")
        cust_win.geometry("+%d+%d" % (rwidth/2, rheight/2))
        def add_customer():
            custid=id_cust.get()
            namecust=name_cust.get()
            addrcust=addr_cust.get()
            gatecust = gate_cust.get()
            priocust = prio_cust.get()

            if len(custid) < 1:
                messagebox.showinfo("SoDIP6", "Customer ID is compulsory")
                return
            elif gatecust not in g.vert_dict.keys():
                messagebox.showerror("SoDIP6", "The gateway router is not correct")
            else:
                C.add_customer(custid,namecust,addrcust,gatecust,priocust)
                row = [custid, namecust, addrcust, gatecust, priocust]
                with open('customer-Details.csv', 'a') as csvFile:
                    writer = csv.writer(csvFile)
                    writer.writerow(row)
                csvFile.close()
                messagebox.showinfo("SoDIP6", "Added Successfully")
                cust_win.destroy()

        frame = LabelFrame(cust_win,text="Add Customer Details)")
        frame.pack()
        Label(frame,text="Customer ID:").grid(row=0,column=0)
        id_cust = Entry(frame)
        id_cust.grid(row=0,column=1)
        Label(frame,text = "Customer Name:").grid(row=1, column=0)
        name_cust = Entry(frame)
        name_cust.grid(row=1, column=1)
        Label(frame,text="Customer Address:").grid(row=2,column=0)
        addr_cust= Entry(frame)
        addr_cust.grid(row=2,column=1)
        Label(frame, text = "Gateway Router:").grid(row=3,column=0)
        gate_cust = Entry(frame)
        gate_cust.grid(row=3,column=1)
        Label(frame, text="Customer Priority").grid(row=4, column=0)
        prio_cust = Entry(frame)
        prio_cust.grid(row=4, column=1)
        addbtn= Button(frame,text="Submit", command=add_customer)
        addbtn.grid(row=5, column=0)
        cancelbtn=Button(frame,text="Cancel", command=lambda : cust_win.destroy())
        cancelbtn.grid(row=5, column=1)
        cust_win.mainloop()

    def view_customers():
        global g
        wincust = Tk()
        wincust.geometry("+%d+%d" %(rwidth/10,rheight/4))
        wincust.title("List Customer Details")
        #wincust.attributes('-topmost',True)
        custframe = LabelFrame(wincust, text="Customer Details")
        custframe.grid(row=0,column=0)
        custlist = C.cust_dict.keys()
        tv = ttk.Treeview(custframe, height=8, selectmode='browse', columns=('Customer Name',
                                                            'Customer Address','Gateway Router','Customer Priority'))
        tv.grid(row=0, column=0, columnspan=2)
        tv.heading('#0', text='Customer ID', anchor=W)
        tv.heading('#1', text='Customer Name', anchor=W)
        tv.heading('#2', text='Customer Address', anchor=W)
        tv.heading('#3', text='Gateway Router', anchor=W)
        tv.heading('#4', text='Customer Priority', anchor=W)

        scrollbar = Scrollbar(wincust, orient="vertical", command=tv.yview)
        scrollbar.grid(row=0, column=1, sticky=NS, pady=(2, 0))
        tv.configure(yscrollcommand=scrollbar.set)

        tosortlist=[]
        for i in custlist:
            custdetails = (C.get_customer(i)).get_customer_details()
            tosortlist.append({"cust": {"id":custdetails["id"], "name":custdetails["custname"],"addr":\
            custdetails["custaddress"],"gw":custdetails["custgateway"],"pr":custdetails["custpriority"]}})

        tosortlist.sort(key=lambda e: e['cust']['pr'], reverse=False)
        for custlist in tosortlist:
            customer=tv.insert('','end',text=custlist['cust']['id'], values=(custlist['cust']['name'],custlist['cust']['addr'],
                                                               custlist['cust']['gw'],custlist['cust']['pr']))
            router_details = ((g.get_router(custlist['cust']['gw'])).get_snmp_details()).values()
            tv.insert(customer,'end',text='Router : '+custlist['cust']['gw'],values=str(router_details))

        def OnDoubleClick(event):
            item = tv.selection()[0]#tv.identify('item', event.x, event.y)
            messagebox.showinfo('SoDIP6',tv.item(item, "values"))
            wincust.focus_force()
        tv.bind("<Double-1>", OnDoubleClick)

    def load_customers():
        global C,g
        global pr_router
        file_open = filedialog.askopenfilename(initialdir='D:\PhD-Study\Experimental\SoDIP6', title='Select file', filetypes=(
            ('CSV files', '*.csv'), ('All files', '*.*')))

        text_display.insert(END,"\n\nLoading customer records and mapping to end routers.......",'a')

        if file_open.endswith('.csv'):
            try:
                with open(file_open) as cust_file:
                    read_file = csv.DictReader(cust_file)
                    pr_list = []
                    for row in read_file:
                        C.add_customer(row['cust_id'], row['cust_name'], row['cust_addr'], row['cust_gateway'],
                                       row['cust_priority'])
                        pr_list.append((row['cust_gateway'],row['cust_priority']))

                    pr_list.sort(key= lambda x: x[1], reverse=True)
                    pr_dict = dict(pr_list)
                    pr_sort = OrderedDict(sorted(pr_dict.items(), key= lambda x: x[1]))
                    pr_router= list(pr_sort.keys())
                    for gw_router in pr_router:
                        g.get_router(gw_router).set_type(type='ASG')
            except (FileNotFoundError, Exception) as e:
                messagebox.showerror('SoDIP6','Customer end router not recognized or file error')
        else:
            messagebox.showerror('SoDIP6', 'Could Not Load file')
            return
        text_display.insert(END, "\nCustomers Successfully Loaded.....", 'a')
        text_display.insert(END, "\nMapped priority routers order is:" + str(pr_router), 'a')

    def add_gw_router():
        global C, g
        global pr_router
        file_open = filedialog.askopenfilename(initialdir='D:\PhD-Study\Experimental\SoDIP6', title='Select file',
                                               filetypes=(
                                                   ('CSV files', '*.csv'), ('All files', '*.*')))

        text_display.insert(END, "\n\nLoading gateway routers and mapping to AS Switch.......", 'a')

        if file_open.endswith('.csv'):
            try:
                with open(file_open) as cust_file:
                    read_file = csv.DictReader(cust_file)
                    pr_list = []
                    for row in read_file:
                        C.add_customer(row['id'], row['name'], row['address'], row['as_gateway'],
                                       row['priority'])
                        g.add_edge(row['id'],row['as_gateway'], weight=10.0)
                        G.add_node(row['as_gateway'])
                        G.add_edge(row['id'],row['as_gateway'], weight=10.0)
                        pr_list.append((row['as_gateway'], row['priority']))

                    pr_list.sort(key=lambda x: x[1], reverse=True)
                    pr_dict = dict(pr_list)
                    pr_sort = OrderedDict(sorted(pr_dict.items(), key=lambda x: x[1]))
                    pr_router = list(pr_sort.keys())
                    for gw_router in pr_router:
                        g.get_router(gw_router).set_type(type='ASG')
            except (FileNotFoundError, Exception) as e:
                messagebox.showerror('SoDIP6', 'Gateway router not recognized or file error')
                print(e)
        else:
            messagebox.showerror('SoDIP6', 'Could Not Load file')
            return
        text_display.insert(END, "\nGateways Successfully Loaded.....", 'a')
        text_display.insert(END, "\nMapped priority routers order is:" + str(pr_router), 'a')

    def details_routers_status():
        global g

        ug_list = [ug_node for ug_node in g.vert_dict.keys() if (g.get_router(ug_node)).get_replace_upgrade() == "U"]
        rp_list = [rp_node for rp_node in g.vert_dict.keys() if (g.get_router(rp_node)).get_replace_upgrade() == "R"]
        plotme.plot_ANFIS_status(G,rp_list,ug_list)

    def status_sp_routers():
        pass  # messure the status of all passed routers using ANFIS
        global g
        st_path = None
        path_cost = None

        for nv in g.vert_dict.keys():
            (g.vert_dict[nv]).visited = False

        text_display.delete('1.0', END)
        fhr, ghr = fhrentry.get(), ghrentry.get()
        if fhr not in g.vert_dict.keys() or ghr not in g.vert_dict.keys():
            messagebox.showerror("SoDIP6", "Shortest path router not recognized")
            return
        try:
            path_cost, st_path = optimal_path(g, fhr, ghr)  # implements dijkstra's shortest path algorithm
        except NameError:
            messagebox.showerror("SoDIP6", "Please Load Network Topology First")
        # print(find_all_paths(G, fhr, ghr))
        strtxt = 'Shortest Path: ' + str(st_path)
        text_display.insert(END, strtxt, 'a')

        if st_path is None:
            text_display.insert(END, "\nCan't identify SP rotuers...")
            return
        for rnode in st_path:
            strtxt = '\nRouter ' + rnode + ' Status:' + \
                     ('upgrade' if(g.get_router(rnode)).get_replace_upgrade()=='U' else 'Replace')
            text_display.insert(END, strtxt, 'a')

    def simulate_migration():
        ghr = ghrentry.get()
        if ghr not in g.vert_dict.keys():
            messagebox.showinfo("SoDIP6", "Please enter gateway router")
            return
        text_display.insert(END,'Starting simulation.......\n','a')
        text_display.delete('1.0', END)

        for mnode in g.get_migrated_list():
            (g.get_router(mnode)).set_migration(False)

        plot_migration_cost = []
        plot_migration_no =[]

        #print(pr_router)

        for sp_router in pr_router:
            path_cost, shortest_path = optimal_path(g, sp_router, ghr)  # implements dijkstra's shortest path algorithm
            if shortest_path is None:
                continue

            strtxt = '\n\nNext Shortest path from ' + sp_router + ' to ' + ghr + ' is: ' + str(shortest_path)
            text_display.insert(END, strtxt, 'a')
            unmigrated_nodes = [v for v in shortest_path if (g.get_router(v)).get_migration() is False]
            if len(unmigrated_nodes)==0:
                text_display.insert(END, "\nThese routers are alreay migrated, no need to calculate cost", 'a')
                continue

            strtxt = str(unmigrated_nodes)
            text_display.insert(END, "\nUnmigrated Nodes are:"+strtxt,'a')

            sp_migration_cost = 0.0
            for rnode in unmigrated_nodes:
                sp_migration_cost += (g.get_router(rnode)).get_migration_cost()
                (g.get_router(rnode)).set_migration(True)
            plot_migration_cost.append(sp_migration_cost)
            plot_migration_no.append(len(unmigrated_nodes))
            strtxt = '\nRouters Migrated:'+str(len(unmigrated_nodes))+' & Migration Cost:'+str(sp_migration_cost)
            text_display.insert(END, strtxt,'a')

        legacy_nodes = g.get_legacy_list()
        if legacy_nodes is not None:
            sp_migration_cost = 0.0
            for rnode in legacy_nodes:
                sp_migration_cost += (g.get_router(rnode)).get_migration_cost()
                (g.get_router(rnode)).set_migration(True)
            plot_migration_cost.append(sp_migration_cost)
            plot_migration_no.append(len(legacy_nodes))
            strtxt = str(legacy_nodes)
            text_display.insert(END, "\nUnmigrated Nodes are:" + strtxt, 'a')
            strtxt = '\nRouters Migrated:' + str(len(legacy_nodes)) + ' & Migration Cost:' + str(sp_migration_cost)
            text_display.insert(END, strtxt, 'a')

        strtxt = "\n\neach path migrated nodes are:"+str(plot_migration_no)+" & \nmigration costs are:"+str(plot_migration_cost)
        text_display.insert(END,strtxt,'a')
        text_display.insert(END,"\n\nSimulation Completed Successfully....ploting graphs...",'a')
        plotme.simulation_plot(plot_migration_no,plot_migration_cost)

    networkmenu.add_command(label="View Graph", command=lambda: plotme.view_networkx_graph(G,g))
    networkmenu.add_command(label='Graphs Details', command=print_graph_details)
    networkmenu.add_command(label='Shortest Path', command=plot_shortest_path)
    networkmenu.add_command(label='add gateways', command=add_gw_router)
    networkmenu.add_command(label='Locate Controller', command=locate_controller)
    menubar.add_cascade(label='Network', menu=networkmenu)

    customermenu=Menu(menubar,tearoff=1)
    customermenu.add_command(label='Add New Customer', command=add_new_customer)
    customermenu.add_command(label="View Customers", command=view_customers)
    customermenu.add_command(label='Load Customers', command=load_customers)
    menubar.add_cascade(label="Customer",menu=customermenu)

    anfismenu=Menu(menubar,tearoff=1)
    fis_file = 'D:\PhD-Study\Experimental\MATLAB-TEST\ANFIS-100EPH22-GBLMF.fis'
    anfismenu.add_command(label="Open ANFIS", command=lambda: eng.fuzzy(fis_file,nargout=0))
    anfismenu.add_command(label='View Rules', command=lambda: eng.ruleview(fis_file,nargout=0))
    anfismenu.add_command(label='View Surfaces', command=lambda: eng.surfview(eng.readfis(fis_file), nargout=0))
    anfismenu.add_command(label="Show Router Status", command=details_routers_status)
    anfismenu.add_command(label="Predict SP Routers", command=status_sp_routers)
    menubar.add_cascade(label="ANFIS",menu=anfismenu)

    graphmenu = Menu(menubar,tearoff=1)
    graphmenu.add_command(label="Joint Budget Estimate", command=lambda:plotme.graph_joint_budget())
    graphmenu.add_command(label="Joint Cost Estimation", command=lambda:plotme.shared_cost_coeff())
    graphmenu.add_command(label="Energy SoDIP6", command=lambda: plotme.energy_plot())
    graphmenu.add_command(label="Evoln. Game Theory", command=lambda: plotme.utility_game_theory())
    graphmenu.add_command(label="Simulate Migration", command=simulate_migration)
    menubar.add_cascade(label="Graphs", menu = graphmenu)

    root.config(menu=menubar)

    root.title("Software Defined IPv6 Network-PhD Thesis By: Babu R Dawadi")
    rwidth = root.winfo_screenwidth() - 100
    rheight = root.winfo_screenheight() - 200
    screen_size = str(rwidth)+'x'+str(rheight)
    root.geometry(screen_size)
    #root.resizable(0,0)  #0,0 for disable resize
    top_frame = LabelFrame(root,borderwidth=1,text="SoDIP6 Entry", bg='#FFCCFF',height=rheight/3,width=rwidth)
    top_frame.pack(side=TOP,expand=True)
    bottom_frame = Frame(root, borderwidth=2, bg='#bbccff', height=2 * rheight / 3, width=rwidth)
    bottom_frame.pack(side=BOTTOM, expand=True)

    canvas1=Canvas(bottom_frame,width=rwidth/1.7, height=rheight/1.5)
    canvas1.pack(side=LEFT)
    canvas2 = Canvas(bottom_frame, width=rwidth/2, height=rheight/1.5)
    canvas2.pack(side=RIGHT)
    img=PIL.ImageTk.PhotoImage(PIL.Image.open("./Figures/SoDIP6-Concept.jpg"))
    canvas1.create_image(0,0,anchor="nw", image=img)
    img1=PIL.ImageTk.PhotoImage(PIL.Image.open("./Figures/Research-UseCase.jpg"))
    canvas2.create_image(0,0,anchor="nw",image=img1)
    #canvas1.addtag_all("all")
    #canvas2.addtag_all("all")


    Label(top_frame,text = "First Hop Router").grid(row=0, column=0)
    fhrentry = Entry(top_frame)
    fhrentry.grid(row=0,column=1)
    Label(top_frame,text="Gateway Router:").grid(row=1,column=0)
    ghrentry = Entry(top_frame)
    ghrentry.grid(row=1,column=1)
    migratebtn = Button(top_frame,text="Migrade Nodes", command=migrate_shortest_path)
    migratebtn.grid(row=0,column=2)

    calculatebtn = Button(top_frame,text="Shortest Path", command=plot_shortest_path)
    calculatebtn.grid(row=1, column=2)
    text_display= Text(top_frame, width = 100, height=5)
    text_display.grid(row=2,columnspan=3)

    for i in tqdm(range(100), desc="Loading..."):
        pass

    root.mainloop()


if __name__ == "__main__":
    main()